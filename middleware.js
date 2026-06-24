export default async function middleware(request) {
  const url = new URL(request.url);

  // Excluir archivos estáticos secundarios (imágenes, CSS, JS auxiliares, favicon, etc.)
  // para evitar solicitar autenticación en recursos que no sean el HTML principal.
  const path = url.pathname;
  if (path.includes('.') && !path.endsWith('.html')) {
    return;
  }

  // 1. Comprobar si el navegador envió la cabecera de autorización
  const authHeader = request.headers.get('authorization');
  if (!authHeader) {
    return new Response('Acceso Requerido', {
      status: 401,
      headers: {
        'WWW-Authenticate': 'Basic realm="Acceso Protegido - ERCMF"',
      },
    });
  }

  // 2. Descodificar las credenciales de Basic Auth (formato usuario:contraseña codificado en Base64)
  const authValue = authHeader.split(' ')[1];
  let username, password;
  try {
    const decoded = atob(authValue);
    const parts = decoded.split(':');
    username = parts[0];
    password = parts.slice(1).join(':'); // Maneja contraseñas que puedan contener dos puntos (:)
  } catch (error) {
    return new Response('Cabecera de autorizacion invalida', { status: 400 });
  }

  // 3. Obtener los usuarios permitidos de Vercel Edge Config
  const edgeConfigUrl = process.env.EDGE_CONFIG;
  if (!edgeConfigUrl) {
    // Si no está configurado (por ejemplo, en desarrollo local), permitimos el paso
    // para evitar bloquearte en tu propia máquina.
    console.warn("La variable de entorno EDGE_CONFIG no está definida. Saltando validación.");
    return;
  }

  try {
    // Transformar la URL de conexión para que apunte al endpoint de items (/items)
    const itemsUrl = new URL(edgeConfigUrl);
    if (!itemsUrl.pathname.endsWith('/items')) {
      itemsUrl.pathname = itemsUrl.pathname.replace(/\/$/, '') + '/items';
    }

    const res = await fetch(itemsUrl.toString());
    if (!res.ok) {
      console.error("Error al obtener Edge Config:", res.statusText);
      return new Response('Error de configuracion en el servidor', { status: 500 });
    }
    
    const users = await res.json();
    
    // Validar si el usuario existe y si su contraseña coincide
    if (users && users[username] === password) {
      return; // Autenticación exitosa, continúa cargando el simulador
    }
  } catch (error) {
    console.error("Fallo al validar credenciales:", error);
    return new Response('Error interno del servidor de autenticacion', { status: 500 });
  }

  // Si las credenciales no son válidas, volvemos a pedir contraseña
  return new Response('Usuario o contraseña incorrectos', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Acceso Protegido - ERCMF"',
    },
  });
}
