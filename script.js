const modal = document.getElementById("modalResultado");
const fecharModal = document.getElementById("fecharModal");
const resultado = document.getElementById("resultado");

document.getElementById("formulario").addEventListener("submit", async function(event) {
  event.preventDefault();

  const produto = document.getElementById("produto").value;
  const dados = {
    produto,
    estado: document.getElementById("estado").value,
    cidade: document.getElementById("cidade").value,
    bairro: document.getElementById("bairro").value,
  };

  const carregando = document.getElementById("carregando");
  carregando.textContent = `🕐 Maravilha! Vamos verificar se "${produto}" é reciclável e encontrar o ponto de coleta mais próximo para você...`;
  carregando.style.display = "block";
  resultado.innerHTML = "";

  try {
    const response = await fetch("http://localhost:5000/reciclagem", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }

    const res = await response.json();

    carregando.style.display = "none";
    const mensagemFormatada = res.mensagem.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    resultado.innerHTML = mensagemFormatada;



    // Abre o modal
    modal.style.display = "flex";

  } catch (error) {
    carregando.style.display = "none";
    resultado.textContent = "❌ Erro ao consultar o backend.";
    modal.style.display = "flex";
    console.error("Erro capturado:", error);
  }
});

// Função para fechar o modal
fecharModal.onclick = function() {
  modal.style.display = "none";
  resultado.innerHTML = "";
};

window.onclick = function(event) {
  if (event.target === modal) {
    modal.style.display = "none";
    resultado.innerHTML = "";
  }
};


