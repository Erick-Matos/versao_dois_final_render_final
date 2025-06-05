document.addEventListener('DOMContentLoaded', () => {
  const baseUrl = window.location.origin;
  const token   = localStorage.getItem('token');
  const admin   = localStorage.getItem('admin') === 'true';
  const userId  = parseInt(localStorage.getItem('userId'), 10);

  if (!token) return window.location.href = '/';

  const jsonHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const btnCriar      = document.querySelector('.btn-anuncio');
  const modal         = document.getElementById('petFormModal');
  const overlay       = modal.querySelector('.modal-overlay');
  const closeModalBtn = document.getElementById('closeModal');
  const petForm       = document.getElementById('petForm');
  const listContainer = document.getElementById('petList');

  function fecharModal() {
    petForm.reset();
    petForm.anuncioId.value        = '';
    petForm.existingImageUrl.value = '';
    modal.classList.remove('active');
  }

  btnCriar?.addEventListener('click', () => modal.classList.add('active'));
  overlay?.addEventListener('click', fecharModal);
  closeModalBtn?.addEventListener('click', fecharModal);

  async function uploadImagem(fileInput) {
    const formData = new FormData();
    formData.append('imagem', fileInput.files[0]);

    const res = await fetch(`${baseUrl}/upload-imagem`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Falha no upload (${res.status})`);
    }

    const data = await res.json();
    return data.image_url;
  }

  async function loadAnuncios() {
    try {
      const res = await fetch(`${baseUrl}/anuncios`, { headers: jsonHeaders });
      const anuncios = await res.json();
      window._anuncios = anuncios;
      renderAnuncios(anuncios);
    } catch (err) {
      alert('Erro ao carregar anúncios');
    }
  }

  function renderAnuncios(anuncios) {
    listContainer.innerHTML = '';
    anuncios.forEach(a => {
      const imgSrc = a.imagem || '/static/img/placeholder.png';
      const card = document.createElement('div');
      card.className = 'pet-card';
      card.innerHTML = `
        <img src="${imgSrc}" alt="${a.titulo}" />
        <div class="pet-info">
          <h2>${a.titulo}</h2>
          <span>Idade: ${a.idade} | Sexo: <span class="sexo">${a.sexo}</span></span><br/>
          <span>Telefone: ${a.telefone}</span>
          <div class="actions">
            <a href="https://wa.me/${a.telefone.replace(/\\D/g, '')}" target="_blank" class="btn-whatsapp">WhatsApp</a>
            ${(admin || a.usuario_id === userId) ? `
              <button class="btn-editar" data-id="${a.id}">Editar</button>
              <button class="btn-excluir" data-id="${a.id}">Excluir</button>
            ` : ''}
            ${a.descricao ? `<span class="descricao-icon" title="Ver descrição" data-desc="${a.descricao}">🛈</span>` : ''}
          </div>
        </div>
      `;
      listContainer.appendChild(card);
    });

    document.querySelectorAll('.btn-excluir').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Excluir anúncio?')) return;
        await fetch(`${baseUrl}/anuncios/${btn.dataset.id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        loadAnuncios();
      });
    });

    document.querySelectorAll('.btn-editar').forEach(btn => {
      btn.addEventListener('click', () => {
        const anuncio = window._anuncios.find(a => a.id == btn.dataset.id);
        if (!anuncio) return alert('Anúncio não encontrado');

        petForm.titulo.value           = anuncio.titulo;
        petForm.descricao.value        = anuncio.descricao || '';
        petForm.idade.value            = anuncio.idade;
        petForm.sexo.value             = anuncio.sexo;
        petForm.existingImageUrl.value = anuncio.imagem || '';
        petForm.anuncioId.value        = anuncio.id;

        let cod = '55', num = '';
        if (anuncio.telefone?.startsWith('+')) {
          const match = anuncio.telefone.match(/^\\+(\\d{1,3})(\\d{8,15})$/);
          if (match) {
            cod = match[1];
            num = match[2];
          }
        }

        petForm.codigoPais.value     = cod;
        petForm.numeroTelefone.value = num;

        modal.classList.add('active');
      });
    });
  }

  petForm.addEventListener('submit', async e => {
    e.preventDefault();

    const idToEdit    = petForm.anuncioId.value;
    const nome        = petForm.titulo.value.trim();
    const descricao   = petForm.descricao.value.trim();
    const idade       = petForm.idade.value.trim();
    const sexo        = petForm.sexo.value;
    const codigoPais  = petForm.codigoPais.value.replace(/\\D/g, '');
    const numeroTel   = petForm.numeroTelefone.value.replace(/\\D/g, '');
    let   imgUrl      = petForm.existingImageUrl.value || '';

    if (!nome || !idade || !codigoPais || !numeroTel || !sexo) {
      return alert('Preencha todos os campos!');
    }

    if (!codigoPais) {
      return alert('Código do país inválido! Use apenas números.');
    }

    if (numeroTel.length < 8 || numeroTel.length > 15) {
      return alert('Telefone inválido! Use só números, de 8 a 15 dígitos.');
    }

    const telefone = `+${codigoPais}${numeroTel}`;

    const fileInput = petForm.imagem;
    if (fileInput && fileInput.files.length) {
      try {
        imgUrl = await uploadImagem(fileInput);
      } catch (err) {
        return alert(err.message);
      }
    }

    const payload = {
      titulo:     nome,
      descricao:  descricao,
      idade:      parseInt(idade, 10),
      sexo:       sexo,
      telefone:   telefone,
      imagem_url: imgUrl
    };

    const url    = idToEdit ? `${baseUrl}/anuncios/${idToEdit}` : `${baseUrl}/anuncios`;
    const method = idToEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: jsonHeaders,
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || `Erro ${res.status}`);

      fecharModal();
      loadAnuncios();
    } catch (err) {
      alert(err.message);
    }
  });

  loadAnuncios();

  const modalDescricao = document.getElementById('descricaoModal');
  const modalTexto     = document.getElementById('descricaoTexto');
  const closeDescricao = document.getElementById('closeDescricaoModal');

  document.addEventListener('click', function (e) {
    if (e.target.classList.contains('descricao-icon')) {
      const texto = e.target.dataset.desc || 'Sem descrição.';
      modalTexto.textContent = texto;
      modalDescricao.classList.add('active');
    }
  });

  closeDescricao?.addEventListener('click', () => {
    modalDescricao.classList.remove('active');
  });
});
