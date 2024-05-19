# preparador-entrevista

## Recomendaciones

Para alinearse a las reglas de desarrollo utilizando vscode, instalar las siguientes extensiones:

* Python Extension Pack
* Pylint
* indent-rainbow

## pre-commit

```pip install pre-commit```

- Instala los hooks definidos en el archivo de configuracion (.pre-commit-config.yaml)
  ```pre-commit install```

- Ejecuta todos los hooks que se encuentran instalados (solo para archivos para el commit)
  ```pre-commit run```

- Actualiza versiones de los hooks a la mas reciente en .pre-commit-config.yaml
  ```pre-commit autoupdate```

## poetry-pre-commit-plugin

- plugin para pre-commit para pre-commit install automaticamente si pre-commit se encuentra instalado.

  ```pip install poetry-pre-commit-plugin==0.1.2```

## Lineamientos

* conventional commits.
* clean architecture.
* inyección de dependencias (patron de diseño)
