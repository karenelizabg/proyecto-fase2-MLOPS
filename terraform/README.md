# P2-06 — Un módulo Terraform por capa

Código de infraestructura AWS, sin despliegue. Los roots `environments/dev` y
`environments/prod` consumen los mismos cuatro módulos locales:

| Módulo | Definición mínima |
|---|---|
| `network` | VPC y dos subredes sin IP pública ni rutas a Internet. RDS requiere dos zonas. |
| `compute` | Una EC2 `t3.micro`, disco cifrado, IMDSv2 y security group sin entrada pública. |
| `data` | Una RDS MariaDB `db.t3.micro`, 20 GiB cifrados y acceso solo desde compute. RDS administra la contraseña en Secrets Manager. |
| `storage` | Un bucket de artefactos con nombre generado, cifrado SSE-S3 y acceso público bloqueado. |

Cada entorno tiene su propia configuración, etiquetas, nombres y estado local
por directorio. Dev usa `10.10.0.0/16`; prod, `10.20.0.0/16`. Ambos usan por defecto
`us-east-1` y dos zonas distintas. No se agregan tamaños ni servicios adicionales
solo por llamarse prod: esta es una base mínima, no una arquitectura de producción.

Los buckets se generarían con prefijos `mlops-p2-dev-artifacts-` y
`mlops-p2-prod-artifacts-`. Son independientes de `mlops-p2-dvc-cache` y
`mlops-p2-dataset-releases`: no se referencian, importan ni modifican esos recursos.
Tampoco se cambian DVC, MinIO, Docker Compose, el portal o el pipeline Python.

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
No hay workflows, GitHub OIDC (P2-07), VPC Gateway Endpoint (P2-15), NAT,
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
