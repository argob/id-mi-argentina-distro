$(function() {
	$('#login').on('click', function() {
		dataLayer.push({
		  'event': 'UAtracking',
		  'ua-category': 'ingresar',
		  'ua-action': 'FOR',
		  'ua-label': 'FOR_LOGIN'
		});
	});

	$('#registerHeader').on('click', function() {
		dataLayer.push({
		  'event': 'UAtracking',
		  'ua-category': 'ingresar',
		  'ua-action': 'FOR',
		  'ua-label': 'FOR_CREAR USUARIO_INICIO_Registrate'
		});
	});

	$('#registerBody').on('click', function() {
		dataLayer.push({
		  'event': 'UAtracking',
		  'ua-category': 'ingresar',
		  'ua-action': 'FOR',
		  'ua-label': 'FOR_CREAR USUARIO_INICIO_' + $(this).text()
		}); 
	});

	$('#register').on('click', function() {
		dataLayer.push({
		  'event': 'UAtracking',
		  'ua-category': 'registro',
		  'ua-action': 'FOR',
		  'ua-label': 'FOR_CREAR USUARIO_FIN'
		}); 
	});

	$('#deleteAccount').on('click', function() {
		dataLayer.push({
		  'event': 'UAtracking',
		  'ua-category': 'eliminar',
		  'ua-action': 'FOR',
		  'ua-label': 'FOR_Eliminar_Cuenta_' + $("#reason").find('option:selected').text()
		}); 
	});

	$('#logout').on('click', function() {
		dataLayer.push({
		  'event': 'UAtracking',
		  'ua-category': 'ingresar',
		  'ua-action': 'FOR',
		  'ua-label': 'FOR_LOGOUT'
		}); 
	});
});