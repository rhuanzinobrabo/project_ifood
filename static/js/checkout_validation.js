/**
 * checkout_validation.js - Validação de formulário para a página de checkout
 * 
 * Este arquivo contém funções para validar os campos do formulário de checkout,
 * fornecendo feedback visual imediato ao usuário e prevenindo o envio de
 * formulários incompletos ou com dados inválidos.
 */

$(document).ready(function() {
    // Campos obrigatórios do formulário
    const requiredFields = [
        'first_name', 
        'last_name', 
        'phone', 
        'email', 
        'address', 
        'city', 
        'pin_code'
    ];
    
    // Padrões de validação para campos específicos
    const validationPatterns = {
        email: {
            pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
            message: 'Por favor, insira um e-mail válido'
        },
        phone: {
            pattern: /^(\(\d{2}\)|\d{2})\s?9?\d{4}-?\d{4}$/,
            message: 'Por favor, insira um telefone válido (ex: (11) 98765-4321)'
        },
        pin_code: {
            pattern: /^\d{5}-?\d{3}$/,
            message: 'Por favor, insira um CEP válido (ex: 12345-678)'
        }
    };
    
    // Adiciona máscara para o campo de telefone
    $('#id_phone').on('input', function() {
        let value = $(this).val().replace(/\D/g, '');
        if (value.length > 0) {
            value = value.replace(/^(\d{2})(\d)/g, '($1) $2');
            value = value.replace(/(\d)(\d{4})$/, '$1-$2');
        }
        $(this).val(value);
    });
    
    // Adiciona máscara para o campo de CEP
    $('#id_pin_code').on('input', function() {
        let value = $(this).val().replace(/\D/g, '');
        if (value.length > 5) {
            value = value.replace(/^(\d{5})(\d)/, '$1-$2');
        }
        $(this).val(value);
    });
    
    // Validação em tempo real dos campos
    $('form input, form select').on('blur', function() {
        validateField($(this));
    });
    
    // Validação ao digitar para campos com padrões específicos
    $('#id_email, #id_phone, #id_pin_code').on('input', function() {
        const fieldName = $(this).attr('name');
        if (validationPatterns[fieldName]) {
            validatePattern($(this), validationPatterns[fieldName]);
        }
    });
    
    // Validação do formulário completo antes do envio
    $('form').on('submit', function(e) {
        let isValid = true;
        
        // Valida todos os campos obrigatórios
        requiredFields.forEach(function(fieldName) {
            const field = $(`#id_${fieldName}`);
            if (!validateField(field)) {
                isValid = false;
            }
        });
        
        // Valida a seleção do método de pagamento
        if (!$('input[name="payment_method"]:checked').val()) {
            $('#payment-method-error').html('Por favor, selecione um método de pagamento');
            isValid = false;
        }
        
        // Impede o envio se houver erros
        if (!isValid) {
            e.preventDefault();
            
            // Exibe mensagem de erro geral
            showFormError('Por favor, corrija os erros no formulário antes de continuar.');
            
            // Rola até o primeiro campo com erro
            const firstError = $('.is-invalid:first');
            if (firstError.length) {
                $('html, body').animate({
                    scrollTop: firstError.offset().top - 100
                }, 500);
            }
        }
    });
    
    // Função para validar um campo individual
    function validateField(field) {
        const fieldName = field.attr('name');
        const value = field.val().trim();
        
        // Verifica se é um campo obrigatório
        if (requiredFields.includes(fieldName) && value === '') {
            showFieldError(field, 'Este campo é obrigatório');
            return false;
        }
        
        // Verifica padrões específicos
        if (validationPatterns[fieldName] && value !== '') {
            return validatePattern(field, validationPatterns[fieldName]);
        }
        
        // Campo válido
        showFieldSuccess(field);
        return true;
    }
    
    // Função para validar um campo contra um padrão específico
    function validatePattern(field, validation) {
        const value = field.val().trim();
        
        if (value === '') {
            // Campo vazio, não valida padrão mas pode ser inválido se for obrigatório
            return validateField(field);
        }
        
        if (!validation.pattern.test(value)) {
            showFieldError(field, validation.message);
            return false;
        }
        
        showFieldSuccess(field);
        return true;
    }
    
    // Exibe erro em um campo específico
    function showFieldError(field, message) {
        // Remove classes de sucesso se existirem
        field.removeClass('is-valid').addClass('is-invalid');
        
        // Cria ou atualiza a mensagem de erro
        let errorElement = field.next('.invalid-feedback');
        if (errorElement.length === 0) {
            errorElement = $('<div class="invalid-feedback"></div>');
            field.after(errorElement);
        }
        
        errorElement.html(message);
    }
    
    // Exibe sucesso em um campo específico
    function showFieldSuccess(field) {
        field.removeClass('is-invalid').addClass('is-valid');
        field.next('.invalid-feedback').remove();
    }
    
    // Exibe mensagem de erro geral do formulário
    function showFormError(message) {
        // Remove mensagens anteriores
        $('.form-error-message').remove();
        
        // Cria nova mensagem
        const errorMessage = $(`
            <div class="alert alert-danger form-error-message mb-3" role="alert">
                <i class="fas fa-exclamation-circle mr-2"></i> ${message}
            </div>
        `);
        
        // Insere no topo do formulário
        $('form').prepend(errorMessage);
    }
    
    // Adiciona estilos CSS para validação
    const validationStyles = `
        <style>
            .form-group {
                margin-bottom: 1rem;
                position: relative;
            }
            
            .form-control.is-invalid {
                border-color: #dc3545;
                padding-right: calc(1.5em + 0.75rem);
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='none' stroke='%23dc3545' viewBox='0 0 12 12'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e");
                background-repeat: no-repeat;
                background-position: right calc(0.375em + 0.1875rem) center;
                background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
            }
            
            .form-control.is-valid {
                border-color: #28a745;
                padding-right: calc(1.5em + 0.75rem);
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 8 8'%3e%3cpath fill='%2328a745' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
                background-repeat: no-repeat;
                background-position: right calc(0.375em + 0.1875rem) center;
                background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
            }
            
            .invalid-feedback {
                display: block;
                width: 100%;
                margin-top: 0.25rem;
                font-size: 80%;
                color: #dc3545;
            }
            
            .payment-method {
                margin-top: 1rem;
                margin-bottom: 1rem;
            }
            
            .payment-method label {
                cursor: pointer;
                margin-right: 1rem;
                padding: 0.5rem;
                border: 1px solid #ced4da;
                border-radius: 0.25rem;
                transition: all 0.2s ease;
            }
            
            .payment-method label:hover {
                border-color: #adb5bd;
            }
            
            .payment-method input[type="radio"]:checked + img {
                border: 2px solid #28a745;
                box-shadow: 0 0 5px rgba(40, 167, 69, 0.5);
            }
        </style>
    `;
    
    // Adiciona os estilos ao head do documento
    $('head').append(validationStyles);
    
    // Melhora a experiência de seleção do método de pagamento
    $('input[name="payment_method"]').on('change', function() {
        // Limpa mensagem de erro
        $('#payment-method-error').html('');
        
        // Destaca a opção selecionada
        $('.payment-method label').removeClass('selected');
        $(this).parent('label').addClass('selected');
    });
});
