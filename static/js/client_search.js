document.addEventListener('DOMContentLoaded', function() {
    const clientInput = document.getElementById('id_client');
    const clientList = document.getElementById('client-list');
    const clientInputContainer = document.getElementById('client-input-container');
    
    if (clientInput && clientList) {
        clientInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length < 2) {
                clientList.innerHTML = '';
                clientList.style.display = 'none';
                return;
            }
            
            fetch('/search_clients/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({query: query})
            })
            .then(response => response.json())
            .then(data => {
                clientList.innerHTML = '';
                
                if (data.error) {
                    const errorItem = document.createElement('div');
                    errorItem.className = 'client-item-error';
                    errorItem.textContent = data.error;
                    clientList.appendChild(errorItem);
                    clientList.style.display = 'block';
                    return;
                }
                
                if (data.message) {
                    const messageItem = document.createElement('div');
                    messageItem.className = 'client-item-message';
                    messageItem.textContent = data.message;
                    clientList.appendChild(messageItem);
                }
                
                if (data.clients && data.clients.length > 0) {
                    data.clients.forEach(client => {
                        const item = document.createElement('div');
                        item.className = 'client-item';
                        item.textContent = client.name;
                        item.dataset.clientId = client.id;
                        item.dataset.clientName = client.name;
                        
                        item.addEventListener('click', function() {
                            clientInput.value = this.dataset.clientName;
                            clientInput.dataset.clientId = this.dataset.clientId;
                            clientList.style.display = 'none';
                        });
                        
                        clientList.appendChild(item);
                    });
                    clientList.style.display = 'block';
                } else {
                    clientList.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                clientList.innerHTML = '<div class="client-item-error">Произошла ошибка при поиске</div>';
                clientList.style.display = 'block';
            });
        });
        
        document.addEventListener('click', function(e) {
            if (!clientInputContainer.contains(e.target)) {
                clientList.style.display = 'none';
            }
        });
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});