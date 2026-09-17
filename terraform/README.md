# P2-06 — Un módulo Terraform por capa

Código de infraestructura AWS, sin despliegue. Los roots `environments/dev` y
`environments/prod` consumen los mismos cuatro módulos locales:

| Módulo | Definición mínima |
|---|---|
| `network` | VPC y dos subredes sin IP pública ni rutas a Internet. RDS requiere dos zonas. |
| `compute` | Una EC2 `t3.micro`, disco cifrado, IMDSv2 y security group sin entrada pública. |
| `data` | Una RDS MariaDB `db.t3.micro`, 20 GiB cifrados, backups retenidos 7 días y acceso solo desde compute. RDS administra la contraseña en Secrets Manager. |
| `storage` | Un bucket de artefactos y otro para sus access logs, con nombres generados, cifrado SSE-S3, bloqueo de acceso público y políticas HTTPS-only. |

Cada entorno tiene su propia configuración, etiquetas, nombres y estado local
por directorio. Dev usa `10.10.0.0/16`; prod, `10.20.0.0/16`. Ambos usan por defecto
`us-east-1` y dos zonas distintas. No se agregan tamaños ni servicios adicionales
solo por llamarse prod: esta es una base mínima, no una arquitectura de producción.

Los buckets se generarían con prefijos `mlops-p2-dev-artifacts-` y
`mlops-p2-prod-artifacts-`. Son independientes de `mlops-p2-dvc-cache` y
`mlops-p2-dataset-releases`: no se referencian, importan ni modifican esos recursos.
Tampoco se cambian DVC, MinIO, Docker Compose, el portal o el pipeline Python.

Los access logs se entregan al bucket independiente `${name}-access-logs-...`,
en el prefijo `access-logs/`. Su policy permite únicamente `s3:PutObject` al
servicio `logging.s3.amazonaws.com`, restringido al ARN del bucket origen y a
la cuenta resuelta mediante `aws_caller_identity`, sin identificadores hardcodeados.
Ambos buckets deniegan acciones S3 sobre el bucket y sus objetos cuando
`aws:SecureTransport` es `false`; esa denegación no concede acceso público.
El receptor no genera access logs hacia sí mismo ni hacia el origen, evitando
recursión según las [recomendaciones de AWS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ServerLogs.html).
No se agregan supresiones de análisis ni se modifican los buckets de P2-04.

## Validación

Requisitos: Terraform CLI >= 1.5 y < 2.0, y acceso al registro para descargar
el provider `hashicorp/aws` 6.x. No se necesitan credenciales AWS, sesión SSO
ni una AMI real para estos comandos; no consultan ni despliegan recursos AWS.
Si falta el ejecutable, instala Terraform siguiendo la
[guía oficial](https://developer.hashicorp.com/terraform/install) antes de continuar.

Desde la raíz del repositorio:

```bash
terraform -chdir=terraform fmt -recursive
terraform -chdir=terraform fmt -check -recursive

terraform -chdir=terraform/environments/dev init -backend=false
terraform -chdir=terraform/environments/dev validate

terraform -chdir=terraform/environments/prod init -backend=false
terraform -chdir=terraform/environments/prod validate
```

Ambos roots referencian los cuatro módulos, por lo que `validate` también
comprueba su configuración. No hay un root adicional en `terraform/`.
Los `.terraform.lock.hcl` se generan por entorno durante `init` y deben conservarse
en Git. No se suministran lockfiles inventados ni se versiona `.terraform/`.

La validación estática comprueba sintaxis, referencias y esquema del provider;
no garantiza permisos, cuotas, compatibilidad de versiones ni un despliegue exitoso.
Referencia: [terraform validate](https://developer.hashicorp.com/terraform/cli/commands/validate).

## Límites del ticket

No ejecutar `apply` ni importar recursos existentes como parte de P2-06.
P2-06 no incluye workflows ni GitHub OIDC (ver P2-07 abajo), VPC Gateway Endpoint (P2-15), NAT,
Internet Gateway, balanceadores, instalación de aplicaciones ni migración de datos.
En particular, la EC2 no tiene conectividad a S3 o Internet ni un mecanismo de
administración remota: la integración operativa corresponde a trabajos posteriores.

Antes de cualquier despliegue futuro habría que seleccionar una AMI real x86_64,
confirmar zonas, versión MariaDB y tamaños admitidos, y revisar conectividad,
permisos y ciclo de vida. RDS usaría una base nueva; no reemplaza MariaDB local.
La política de snapshot final y la conservación del contenido S3 también deben
revisarse antes de una futura eliminación de infraestructura.

Los archivos `terraform.tfvars.example` contienen solo parámetros no sensibles.
No incluyas perfiles personales, access keys, contraseñas o tokens en Terraform.
El provider no fija una identidad: cualquier futura autenticación se resolvería
fuera del código. Los estados, planes y variables locales están ignorados.

## P2-07 — GitHub Actions con OIDC

El root independiente `bootstrap/github-oidc` define un IAM OIDC provider para
`https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`, y
el rol `mlops-p2-github-oidc`. No depende de los módulos de P2-06 ni los despliega.
No se adjuntan políticas de acceso a recursos al rol: este ticket comprueba solo
autenticación. `sts:GetCallerIdentity` no necesita permisos adicionales.

La trust policy permite `sts:AssumeRoleWithWebIdentity` exclusivamente con
`aud = sts.amazonaws.com` y
`sub = repo:karenelizabg/proyecto-fase2-MLOPS:ref:refs/heads/main`.
No permite otros repositorios, ramas, tags, pull requests ni subjects de GitHub
Environments. El job OIDC no declara `environment` para conservar ese subject.

### Validación estática y prueba real

El workflow `.github/workflows/terraform-oidc.yml` valida los tres roots en PRs
hacia `main`, pushes a `main` y ejecuciones manuales. El job de validación solo
tiene `contents: read`; no intenta asumir un rol ni necesita credenciales AWS.
Las Actions están fijadas a commits verificados de sus repositorios oficiales.

Además de los comandos de P2-06, valida el nuevo root con:

```bash
terraform -chdir=terraform fmt -recursive
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform/bootstrap/github-oidc init -backend=false
terraform -chdir=terraform/bootstrap/github-oidc validate
```

El job OIDC depende de la validación y solo corre en el repositorio exacto, desde
`main`, por push o ejecución manual. Tiene `contents: read` e `id-token: write`,
utiliza `aws-actions/configure-aws-credentials` con
`role-to-assume: ${{ vars.AWS_ROLE_ARN }}` y una sesión de 15 minutos. La prueba
STS descarta su salida y no imprime identificadores de identidad.

La validación del código no demuestra una autenticación real. Esta última queda
pendiente hasta que una persona autorizada cree el provider/rol fuera de esta
tarea y registre el output `role_arn` como variable de repositorio `AWS_ROLE_ARN`
en GitHub. El ARN no es una credencial y no necesita escribirse en los archivos.
Sin la variable o sin el rol real, el job OIDC en `main` falla explícitamente;
los PRs no ejecutan ese job y no fallan por falta de autorización de su rama.

### Provider existente y seguridad

Antes de una futura creación, comprueba si la cuenta ya tiene el provider GitHub.
Si existe, suministra su ARN mediante `TF_VAR_existing_oidc_provider_arn` o un
archivo de variables local ignorado. Verifica que pertenece a la cuenta destino
y que tiene la URL y audience indicadas. En ese modo Terraform no crea, importa
ni modifica ese provider; únicamente lo referencia en la trust policy del rol.
No cambies entre modos sobre un estado que ya gestione el provider sin revisar
su ciclo de vida: podría proponer eliminarlo. No se hace esa transición aquí.

La creación inicial requiere una identidad humana autorizada externa al proyecto;
el workflow no puede crear su propio rol de arranque. No se guardan perfiles
personales, credenciales estáticas, tokens ni identificadores de cuenta en código.
No se ejecutan `plan`, `apply` ni importaciones como parte de esta implementación.
No se agregan permisos S3, EC2, RDS, IAM o Secrets Manager, ni recursos de P2-15.

## P2-15 — Buckets S3 versionados + VPC Gateway Endpoint

Extiende los módulos `storage` y `network` de P2-06; no agrega un root nuevo,
por lo que ya queda cubierto por la validación existente (`environments/dev`
y `environments/prod` consumen ambos módulos).

`modules/storage` agrega dos buckets independientes de `this`
(el bucket de artefactos de P2-06): `dvc_cache` y `dataset_releases`, con
`aws_s3_bucket_versioning` habilitado y el mismo baseline de seguridad que
ya usa el módulo (bloqueo de acceso público, cifrado SSE-S3, deny
HTTPS-only, access logs entregados al mismo bucket `logs` de P2-06, cada
uno bajo su propio prefijo `access-logs/dvc-cache/` y
`access-logs/dataset-releases/`). La policy de `logs` se amplió para
permitir la entrega de logs desde estos dos buckets además de `this`.
Igual que en P2-06, los nombres se generan con `bucket_prefix` (p. ej.
`mlops-p2-dev-dvc-cache-<sufijo>`): son independientes de
`mlops-p2-dvc-cache` y `mlops-p2-dataset-releases` (los buckets reales de
P2-04); no se referencian, importan ni modifican.

`modules/network` agrega un `aws_vpc_endpoint` tipo Gateway para S3,
asociado a la route table por defecto de la VPC — la única que existe,
porque P2-06 no crea route tables propias (las subredes no tienen rutas
públicas). El nombre del servicio se resuelve con `data "aws_region"
"current"`, sin región hardcodeada.

No se ejecuta `apply` ni se modifica ningún recurso real de AWS como parte
de este ticket, igual que P2-06 y P2-07.
