/**
 * cart_debug.js - Script para depuração e garantia de funcionamento do carrinho
 * 
 * Este arquivo contém funções para verificar e garantir o funcionamento correto
 * da integração JavaScript do carrinho, especialmente na página de detalhes do restaurante.
 */

$(document).ready(function() {
    console.log('cart_debug.js carregado com sucesso');
    
    // Verifica se os botões do carrinho existem na página
    const addButtons = $('.add_to_cart');
    const decreaseButtons = $('.decrease_cart');
    
    console.log('Botões de adicionar encontrados: ' + addButtons.length);
    console.log('Botões de diminuir encontrados: ' + decreaseButtons.length);
    
    // Verifica se os botões têm os atributos necessários
    addButtons.each(function(index) {
        const dataId = $(this).attr('data-id');
        const dataUrl = $(this).attr('data-url');
        console.log(`Botão adicionar #${index}: data-id=${dataId}, data-url=${dataUrl}`);
    });
    
    // Sobrescreve o evento de clique para garantir funcionamento
    $('.add_to_cart').off('click').on('click', function(e) {
        e.preventDefault();
        console.log('Botão de adicionar clicado');
        
        const foodId = $(this).attr('data-id');
        const url = $(this).attr('data-url');
        
        console.log(`Adicionando item: ID=${foodId}, URL=${url}`);
        
        // Adicionar efeito visual ao botão
        $(this).addClass('btn-loading');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                console.log('Resposta do servidor:', response);
                
                if(response.status == 'login_required') {
                    alert('É necessário fazer login para adicionar itens ao carrinho');
                    window.location = '/login';
                } else if(response.status == 'Failed') {
                    alert(response.message);
                } else {
                    // Atualiza o contador do carrinho
                    if(response.cart_counter) {
                        $('#cart_counter').html(response.cart_counter['cart_count']);
                    }
                    
                    // Atualiza a quantidade do item
                    if(response.qty) {
                        $('#qty-'+foodId).html(response.qty);
                    }
                    
                    // Atualiza os valores do carrinho
                    if(response.cart_amount) {
                        updateCartValues(
                            response.cart_amount['subtotal'],
                            response.cart_amount['tax_dict'],
                            response.cart_amount['grand_total']
                        );
                    }
                    
                    // Exibe notificação de sucesso
                    showNotification('Item adicionado ao carrinho!');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro ao adicionar item:', error);
                console.error('Status:', status);
                console.error('Resposta:', xhr.responseText);
                alert('Erro ao adicionar item ao carrinho. Verifique o console para mais detalhes.');
            },
            complete: function() {
                // Remove o efeito de carregamento
                $('.add_to_cart[data-id="'+foodId+'"]').removeClass('btn-loading');
            }
        });
    });
    
    // Sobrescreve o evento de clique para diminuir quantidade
    $('.decrease_cart').off('click').on('click', function(e) {
        e.preventDefault();
        console.log('Botão de diminuir clicado');
        
        const foodId = $(this).attr('data-id');
        const url = $(this).attr('data-url');
        const cartId = $(this).attr('id');
        
        console.log(`Diminuindo item: ID=${foodId}, URL=${url}`);
        
        // Adicionar efeito visual ao botão
        $(this).addClass('btn-loading');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                console.log('Resposta do servidor:', response);
                
                if(response.status == 'login_required') {
                    alert('É necessário fazer login para gerenciar o carrinho');
                    window.location = '/login';
                } else if(response.status == 'Failed') {
                    alert(response.message);
                } else {
                    // Atualiza o contador do carrinho
                    if(response.cart_counter) {
                        $('#cart_counter').html(response.cart_counter['cart_count']);
                    }
                    
                    // Atualiza a quantidade do item
                    if(response.qty !== undefined) {
                        $('#qty-'+foodId).html(response.qty);
                    }
                    
                    // Atualiza os valores do carrinho
                    if(response.cart_amount) {
                        updateCartValues(
                            response.cart_amount['subtotal'],
                            response.cart_amount['tax_dict'],
                            response.cart_amount['grand_total']
                        );
                    }
                    
                    // Exibe notificação
                    showNotification('Carrinho atualizado!');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro ao diminuir item:', error);
                console.error('Status:', status);
                console.error('Resposta:', xhr.responseText);
                alert('Erro ao atualizar o carrinho. Verifique o console para mais detalhes.');
            },
            complete: function() {
                // Remove o efeito de carregamento
                $('.decrease_cart[data-id="'+foodId+'"]').removeClass('btn-loading');
            }
        });
    });
    
    // Função para atualizar os valores do carrinho
    function updateCartValues(subtotal, tax_dict, grand_total) {
        console.log('Atualizando valores do carrinho:');
        console.log('Subtotal:', subtotal);
        console.log('Taxas:', tax_dict);
        console.log('Total:', grand_total);
        
        // Se a função applyCartAmounts existir, use-a
        if(typeof window.applyCartAmounts === 'function') {
            window.applyCartAmounts(subtotal, tax_dict, grand_total);
        }
    }
    
    // Função para exibir notificação
    function showNotification(message) {
        const notification = $('<div class="cart-notification"></div>');
        notification.html('<p>'+message+'</p><span class="close-button">&times;</span>');
        notification.css({
            'position': 'fixed',
            'bottom': '20px',
            'right': '20px',
            'padding': '10px 15px',
            'background-color': '#28a745',
            'color': 'white',
            'border-radius': '4px',
            'box-shadow': '0 2px 10px rgba(0,0,0,0.2)',
            'z-index': '9999'
        });
        
        $('body').append(notification);
        
        // Remove automaticamente após 3 segundos
        setTimeout(function() {
            notification.fadeOut(300, function() {
                $(this).remove();
            });
        }, 3000);
    }
    
    // Inicializa as quantidades dos itens
    function initializeItemQuantities() {
        console.log('Inicializando quantidades dos itens');
        
        // Busca as quantidades atuais do carrinho
        $.ajax({
            type: 'GET',
            url: '/mercado/cart/',
            success: function(response) {
                console.log('Dados do carrinho obtidos');
                
                // Extrai as quantidades dos itens do HTML da resposta
                const parser = new DOMParser();
                const htmlDoc = parser.parseFromString(response, 'text/html');
                
                // Busca todos os elementos com a classe item_qty
                const itemQtys = htmlDoc.querySelectorAll('.item_qty');
                
                console.log('Itens encontrados no carrinho:', itemQtys.length);
                
                // Atualiza as quantidades na página atual
                itemQtys.forEach(function(item) {
                    const id = item.getAttribute('id');
                    const qty = item.getAttribute('data-qty');
                    const foodId = id.replace('qty-', '');
                    
                    console.log(`Item ${foodId}: quantidade = ${qty}`);
                    
                    // Atualiza a quantidade exibida
                    $('#qty-'+foodId).html(qty);
                });
            },
            error: function(xhr, status, error) {
                console.error('Erro ao obter dados do carrinho:', error);
            }
        });
    }
    
    // Inicializa as quantidades ao carregar a página
    initializeItemQuantities();
});
