# Tailwind Theme (Django)

## Estructura
- theme/
  - src/styles.css  -> entrada
  - static/css/dist/styles.css -> salida
  - tailwind.config.js
  - postcss.config.js
  - package.json

## Pasos (Windows)
1) Desde `calidad_project/theme`:
   npm install

2) Compilación en desarrollo (con watch):
   npm run dev

   (Opcional) Desde Django:
   python manage.py tailwind start
   *Esto ejecutará `npm run dev` internamente.*

3) Build para producción:
   npm run build

Si no se aplican estilos, verifica que tus plantillas HTML están dentro de las rutas configuradas en `tailwind.config.js` (carpeta templates).
