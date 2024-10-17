// api.js

// Função para obter o token do localStorage
function getToken() {
    return localStorage.getItem('auth-token');
}

// Função para fazer uma requisição GET
async function apiGet(url) {
    const token = getToken();
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'auth-token': token, // Adiciona o token ao cabeçalho
        }
    });
    return response;
}

// Função para fazer uma requisição POST
async function apiPost(url, data) {
    const token = getToken();
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'auth-token': token, // Adiciona o token ao cabeçalho
        },
        body: new URLSearchParams(data) // Converte dados para o formato correto
    });
    return response;
}

// As funções estarão disponíveis globalmente
