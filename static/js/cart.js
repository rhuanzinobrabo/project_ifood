/**
 * cart.js - Funções para gerenciamento do carrinho de compras
 * 
 * Este arquivo contém as funções necessárias para adicionar, remover e
 * atualizar itens no carrinho de compras, com feedback visual para o usuário.
 */

$(document).ready(function() {
    console.log('cart.js carregado com sucesso');
    
    // Adicionar item ao carrinho
    $(document).on('click', '.add_to_cart', function(e) {
        e.preventDefault();
        
        let food_id = $(this).attr('data-id');
        let url = $(this).attr('data-url');
        
        console.log('Adicionando item ao carrinho:', food_id, url);
        
        // Adicionar efeito visual ao botão
        $(this).addClass('btn-loading');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                console.log('Resposta do servidor:', response);
                
                if(response.status == 'login_required') {
                    window.location = '/login';
                } else if(response.status == 'Failed') {
                    showCartNotification(response.message, 'danger');
                } else {
                    // Atualiza o contador do carrinho
                    if(response.cart_counter) {
                        $('#cart_counter').html(response.cart_counter['cart_count']);
                        $('#cart_counter').addClass('highlight');
                        setTimeout(function() {
                            $('#cart_counter').removeClass('highlight');
                        }, 500);
                    }
                    
                    // Atualiza a quantidade do item
                    if(response.qty) {
                        $('#qty-'+food_id).html(response.qty);
                    }
                    
                    // Atualiza os valores do carrinho
                    if(response.cart_amount) {
                        applyCartAmounts(
                            response.cart_amount['subtotal'],
                            response.cart_amount['tax_dict'],
                            response.cart_amount['grand_total']
                        );
                    }
                    
                    // Exibe notificação de sucesso
                    showCartNotification('Item adicionado ao carrinho!', 'success');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro ao adicionar item:', error);
                showCartNotification('Erro ao adicionar item ao carrinho', 'danger');
            },
            complete: function() {
                // Remove o efeito de carregamento
                $('.add_to_cart[data-id="'+food_id+'"]').removeClass('btn-loading');
            }
        });
    });
    
    // Diminuir quantidade do item no carrinho
    $(document).on('click', '.decrease_cart', function(e) {
        e.preventDefault();
        
        let food_id = $(this).attr('data-id');
        let url = $(this).attr('data-url');
        let cart_id = $(this).attr('id');
        
        console.log('Diminuindo quantidade:', food_id, url);
        
        // Adicionar efeito visual ao botão
        $(this).addClass('btn-loading');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                console.log('Resposta do servidor:', response);
                
                if(response.status == 'login_required') {
                    window.location = '/login';
                } else if(response.status == 'Failed') {
                    showCartNotification(response.message, 'danger');
                } else {
                    // Atualiza o contador do carrinho
                    if(response.cart_counter) {
                        $('#cart_counter').html(response.cart_counter['cart_count']);
                    }
                    
                    // Atualiza a quantidade do item
                    if(response.qty !== undefined) {
                        $('#qty-'+food_id).html(response.qty);
                    }
                    
                    // Atualiza os valores do carrinho
                    if(response.cart_amount) {
                        applyCartAmounts(
                            response.cart_amount['subtotal'],
                            response.cart_amount['tax_dict'],
                            response.cart_amount['grand_total']
                        );
                    }
                    
                    // Se o item foi removido completamente
                    if(window.location.pathname.includes('cart') && response.qty == 0) {
                        removeCartItem(cart_id);
                    }
                    
                    // Exibe notificação
                    showCartNotification('Carrinho atualizado!', 'info');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro ao diminuir quantidade:', error);
                showCartNotification('Erro ao atualizar o carrinho', 'danger');
            },
            complete: function() {
                // Remove o efeito de carregamento
                $('.decrease_cart[data-id="'+food_id+'"]').removeClass('btn-loading');
            }
        });
    });
    
    // Remover item do carrinho
    $(document).on('click', '.delete_cart', function(e) {
        e.preventDefault();
        
        let cart_id = $(this).attr('data-id');
        let url = $(this).attr('data-url');
        
        console.log('Removendo item do carrinho:', cart_id, url);
        
        // Adicionar efeito visual ao item
        $('#cart-item-'+cart_id).addClass('removing');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                console.log('Resposta do servidor:', response);
                
                if(response.status == 'Failed') {
                    showCartNotification(response.message, 'danger');
                    $('#cart-item-'+cart_id).removeClass('removing');
                } else {
                    // Atualiza o contador do carrinho
                    $('#cart_counter').html(response.cart_counter['cart_count']);
                    
                    // Remove o item do carrinho
                    removeCartItem(cart_id);
                    
                    // Atualiza os valores do carrinho
                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    );
                    
                    // Exibe notificação
                    showCartNotification('Item removido do carrinho!', 'info');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro ao remover item:', error);
                showCartNotification('Erro ao remover item do carrinho', 'danger');
                $('#cart-item-'+cart_id).removeClass('removing');
            }
        });
    });
    
    // Função para remover item do carrinho com animação
    function removeCartItem(cart_id) {
        $('#cart-item-'+cart_id).fadeOut(300, function() {
            $(this).remove();
            
            // Verifica se o carrinho está vazio
            if($('.cart-item').length === 0) {
                $('#empty-cart').removeClass('d-none');
                $('.btn-place-order').addClass('d-none');
            }
        });
    }
    
    // Função para exibir notificação
    function showCartNotification(message, type) {
        // Define a cor de fundo com base no tipo
        let bgColor = '#28a745'; // success (verde)
        if(type === 'danger') {
            bgColor = '#dc3545'; // danger (vermelho)
        } else if(type === 'info') {
            bgColor = '#17a2b8'; // info (azul)
        } else if(type === 'warning') {
            bgColor = '#ffc107'; // warning (amarelo)
        }
        
        // Cria o elemento de notificação
        const notification = $('<div class="cart-notification"></div>');
        notification.html('<p>'+message+'</p><span class="close-button">&times;</span>');
        notification.css('background-color', bgColor);
        
        // Adiciona ao corpo da página
        $('body').append(notification);
        
        // Adiciona evento de clique para fechar
        notification.find('.close-button').on('click', function() {
            notification.fadeOut(300, function() {
                $(this).remove();
            });
        });
        
        // Remove automaticamente após 3 segundos
        setTimeout(function() {
            notification.fadeOut(300, function() {
                $(this).remove();
            });
        }, 3000);
    }
    
    // Inicializa as quantidades dos itens no carregamento da página
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
