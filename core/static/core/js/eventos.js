// Cargar tipos de evento
fetch('/api/tipos-evento/')
.then(response => {
    if (!response.ok) {
        throw new Error('Error al obtener los tipos de evento');
    }
    return response.json();
})
.then(data => {
    const select = document.getElementById('tipo_evento');
    data.forEach(tipo => {
        const option = document.createElement('option');
        option.value = tipo.id;
        option.textContent = tipo.nombre;
        select.appendChild(option);
    });
})
.catch(error => {
    console.error('Error al cargar los tipos de evento:', error);
    alert('No se pudieron cargar los tipos de evento');
});