<img src="/id/static/img/miargentina.png" alt="MiArgentina" width="400"/>

# Autenticación Mi Argentina

Esta es una distribución pública del sistema de autenticación de Mi Argentina (basado en la especificación OpenID Connect), el portal digital del ciudadano desarrollado por la Subsecretaría de Gobierno Digital de la República Argentina en el periodo 2015-2019.

La intención de esta distribución es la reutilización por parte de gobierno nacionales y subnacionales que deseen construir sus plataforma de servicios para ciudadanos.

Esta versión cuenta con las siguientes funcionalidades:

- Inicio de sesión
- Registro
- Recupero de contraseña
- Flujo de verificación de correo electrónico
- Envío de mails
- ABM de datos de la cuenta
- Borrar cuenta
- ABM de clientes OpenID
- Configuración de scopes OpenID
- Middlewares
- Tracking de errores

## Dependencias y Requisitos
- Python >= 3.6
- PostgreSQL >= 10
- Redis >= 4.0.9

## Clonar el proyecto
```bash
$ git clone https://github.com/argob/id-mi-argentina-distro.git
```

## Crear entorno virtual (virtuallenv)
```bash
$ cd id-mi-argentina-distro/
$ python3 -m venv .venv
```

## Crear el archivo settings_custom.py
```bash
$ cp settings_custom.py.edit settings_custom.py
```
> NOTA: configurar las credenciales de la base de datos en DATABASES

## Instalación de paquetes, migraciones, fixtures y creación de superuser
```bash
$ ./manage.py setup
```

## Ejecutar el proyecto
```bash
$ ./manage.py runserver

System check identified no issues (0 silenced).
December 03, 2019 - 14:28:15
Django version 2.1.7, using settings 'id.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## Middlewares

```bash
MIDDLEWARE = [
    ...
    # Verificación obligatorio del correo electrónico
    'id.middleware.EmailValidatedMiddleware',

    # Términos y condiciones obligatorio
    'id.middleware.TermsAndConditionsMiddleware',
]
```

## Envío de correo electrónico

En este caso pongo MailGun, a modo de ejemplo, como proveedor de envío de correo electrónico.
[En este link podes ver la documentación del package](https://anymail.readthedocs.io/en/stable/).

```bash
ANYMAIL = {
    'MAILGUN_API_KEY': '',
    'MAILGUN_SENDER_DOMAIN': '',
}
```

## Django OIDC Provider

### Configuración

#### OpenID Connect Session Management

Habilita OpenID Connect Session Management 1.0 para monitorear el estado del login del usuario final. [Ver más detalle](https://django-oidc-provider.readthedocs.io/en/latest/sections/sessionmanagement.html#sessionmanagement)

```bash
MIDDLEWARE_CLASSES = [
    ...
    'oidc_provider.middleware.SessionManagementMiddleware',
]
OIDC_SESSION_MANAGEMENT_ENABLE = True
OIDC_UNAUTHENTICATED_SESSION_MANAGEMENT_KEY = ''
```

#### Configuraciones adicionales
* [OIDC_IDTOKEN_PROCESSING_HOOK](https://django-oidc-provider.readthedocs.io/en/latest/sections/settings.html#oidc-idtoken-processing-hook)

```bash
OIDC_IDTOKEN_PROCESSING_HOOK = 'id.oidc_provider_settings.default_idtoken_processing_hook'
```

* [OIDC_IDTOKEN_SUB_GENERATOR](https://django-oidc-provider.readthedocs.io/en/latest/sections/settings.html#oidc-idtoken-sub-generator)

```bash
OIDC_IDTOKEN_SUB_GENERATOR = 'id.oidc_provider_settings.custom_sub_generator'
```

* [OIDC_EXTRA_SCOPE_CLAIMS](https://django-oidc-provider.readthedocs.io/en/latest/sections/settings.html#oidc-extra-scope-claims)

```bash
OIDC_EXTRA_SCOPE_CLAIMS = 'id.oidc_provider_settings.CustomScopeClaims'
```

* [OIDC_USERINFO](https://django-oidc-provider.readthedocs.io/en/latest/sections/settings.html#oidc-userinfo)

```bash
OIDC_USERINFO = 'id.oidc_provider_settings.userinfo'
```

### Alta de un cliente OIDC

El alta se encuentra en la sección [http://localhost:8000/admin/oidc_provider/client/](http://localhost:8000/admin/oidc_provider/client/)

* `confidential`: Clientes capaces de mantener la confidencialidad de sus credenciales (por ejemplo, cliente implementado en un servidor seguro con acceso restringido a las credenciales del cliente).

* `public`: Clientes que no son capaces de mantener la confidencialidad de sus credenciales (por ejemplo, clientes que se ejecutan en el dispositivo utilizado por el propietario del recurso, como una aplicación nativa instalada o una aplicación basada en navegador web), y tampoco capaces de asegurar la autenticación del cliente por cualquier otro medio.

* `name`: Nombre legible de tu cliente OpenID
* `client_type`: Los valores son `confidential` o `public`
* `client_id`: Identificación única del cliente
* `client_secret`: Valor secreto para aplicaciones confidenciales
* `response_types`: Los flujos y los valores asociados `response_type` que puede utilizar el cliente
* `jwt_alg`: Los clientes pueden elegir qué algoritmo se utilizará para firmar id_tokens. Los valores son HS256 y RS256
* `date_created`: La fecha se añade automáticamente cuando se crea
* `redirect_uris`: Lista de URIs de redirección
* `require_consent`: Si esta opción está seleccionada, el servidor nunca pedirá consentimiento (sólo se aplica a clientes confidenciales).
* `reuse_consent`: Si está habilitado, el Servidor guardará el consentimiento del usuario dado a un cliente específico, de modo que no se le pedirá al usuario la misma autorización varias veces.

[Documentación completa del package Django OIDC Provider](https://django-oidc-provider.readthedocs.io/en/latest/)
