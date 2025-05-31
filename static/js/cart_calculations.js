/**
 * cart_calculations.js - Funções para cálculos precisos do carrinho
 * 
 * Este arquivo contém as funções necessárias para calcular corretamente
 * os valores do carrinho, incluindo subtotal, taxas e total geral.
 */

// Função para garantir que os valores sejam tratados como números
function ensureNumeric(value) {
    if (typeof value === 'string') {
        // Remove caracteres não numéricos, exceto ponto decimal
        return parseFloat(value.replace(/[^\d.-]/g, '')) || 0;
    }
    return parseFloat(value) || 0;
}

// Função para formatar valores monetários no padrão brasileiro
function formatCurrency(value) {
    const numericValue = ensureNumeric(value);
    return 'R$ ' + numericValue.toFixed(2).replace('.', ',');
}

// Função principal para aplicar os valores do carrinho
function applyCartAmounts(subtotal, tax_dict, grand_total) {
    console.log('Aplicando valores do carrinho:', subtotal, tax_dict, grand_total);
    
    // Converte valores para números
    const subtotalValue = ensureNumeric(subtotal);
    const grandTotalValue = ensureNumeric(grand_total);
    
    // Atualiza o subtotal com animação
    updateValueWithAnimation('#subtotal', subtotalValue);
    
    // Atualiza as taxas
    if (tax_dict) {
        Object.keys(tax_dict).forEach(function(key) {
            const taxValue = ensureNumeric(tax_dict[key]);
            updateValueWithAnimation('#tax-' + key, taxValue);
        });
    }
    
    // Atualiza o total geral com animação
    updateValueWithAnimation('#total', grandTotalValue);
    
    // Verifica se o carrinho está vazio
    if (grandTotalValue <= 0) {
        $('#empty-cart').removeClass('d-none');
        $('.btn-place-order').addClass('d-none');
    } else {
        $('#empty-cart').addClass('d-none');
        $('.btn-place-order').removeClass('d-none');
    }
}

// Função para atualizar valores com animação
function updateValueWithAnimation(selector, newValue) {
    const element = $(selector);
    if (element.length === 0) return;
    
    // Obtém o valor atual
    const currentText = element.text();
    const currentValue = ensureNumeric(currentText);
    
    // Formata o novo valor
    const formattedValue = formatCurrency(newValue);
    
    // Aplica classe de destaque com base na mudança de valor
    if (newValue > currentValue) {
        element.addClass('price-increase');
        setTimeout(function() {
            element.removeClass('price-increase');
        }, 1000);
    } else if (newValue < currentValue) {
        element.addClass('price-decrease');
        setTimeout(function() {
            element.removeClass('price-decrease');
        }, 1000);
    }
    
    // Aplica o novo valor com animação
    element.addClass('highlight-change');
    element.text(formattedValue);
    
    // Remove a classe de destaque após a animação
    setTimeout(function() {
        element.removeClass('highlight-change');
    }, 700);
}

// Exporta as funções para uso global
window.applyCartAmounts = applyCartAmounts;
window.formatCurrency = formatCurrency;
window.ensureNumeric = ensureNumeric;
