function cleanFormErrors() {
    $('select').change(function() {
        var parent = $(this).parent();
        parent.removeClass('has-error');
        parent.find('p').remove();
    });

    $('input').keypress(function() {
        var parent = $(this).parent();
        parent.removeClass('has-error');
        parent.find('p').remove();
    });

    $('.btn-group').click(function() {
        var parent = $(this).parent();
        parent.removeClass('has-error');
        parent.find('p').remove();
    });

    $('input').change(function() {
        var parent = $(this).parent();
        parent.removeClass('has-error');
        parent.find('p').remove();
    });
}

$('input[name="email"]').on('copy paste cut drag drop', function() {
    return false;
});
$('input[name="email_confirmation"]').on('copy paste cut drag drop', function() {
    return false;
});

function toggleShowHidePassword(mostrar) {
    mostrar.addEventListener("click", (e) => {
        e.preventDefault();
        let clave = document.getElementById('password');

        if(clave.type === 'password') {
            clave.setAttribute("type", "text");
            mostrar.innerHTML = '<input id="opcion" name="mostrar" type="checkbox" checked value="">Ocultar la contraseña';
            document.getElementById('password').focus();
        } else {
            clave.setAttribute("type", "password");
            mostrar.innerHTML = '<input id="opcion" name="mostrar" type="checkbox" value="">Mostrar la contraseña';
            document.getElementById('mostrar').focus();
        }
    });
}
