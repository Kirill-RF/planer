document.addEventListener('DOMContentLoaded', function() {
    const clientInput = document.getElementById('id_client');
    const clientList = document.getElementById('client-list');
    const clientInputContainer = document.getElementById('client-input-container');
    
    if (clientInput && clientList) {
        let searchTimeout = null;
        
        // Function to perform search
        function performSearch(query) {
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
                            document.getElementById('selected_client_id').value = this.dataset.clientId;
                            clientList.style.display = 'none';
                        });
                        
                        clientList.appendChild(item);
                    });
                    clientList.style.display = 'block';
                } else {
                    const noResultsItem = document.createElement('div');
                    noResultsItem.className = 'client-item-message';
                    noResultsItem.textContent = data.message || 'Клиенты не найдены';
                    clientList.appendChild(noResultsItem);
                    clientList.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                clientList.innerHTML = '<div class="client-item-error">Произошла ошибка при поиске</div>';
                clientList.style.display = 'block';
            });
        }
        
        // Handle input with debouncing to improve performance
        clientInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            // Clear the previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Set a new timeout to delay the search
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300); // 300ms delay
        });
        
        // Add search button for immediate search
        const searchButton = document.createElement('button');
        searchButton.type = 'button';
        searchButton.className = 'btn btn-outline-secondary';
        searchButton.textContent = 'Поиск';
        searchButton.style.marginLeft = '5px';
        searchButton.style.verticalAlign = 'top';
        searchButton.title = 'Найти клиентов по введенному тексту';
        
        searchButton.addEventListener('click', function() {
            const query = clientInput.value.trim();
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            performSearch(query);
        });
        
        // Insert the search button next to the input field
        const inputGroup = document.createElement('div');
        inputGroup.className = 'input-group';
        clientInput.parentNode.insertBefore(inputGroup, clientInput);
        inputGroup.appendChild(clientInput);
        inputGroup.appendChild(searchButton);
        
        // Add styling to the input group
        inputGroup.style.display = 'flex';
        
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