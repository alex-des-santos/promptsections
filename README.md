# 🎨 Prompt Sections - Stable Diffusion

## 📌 Visão Geral

**Prompt Sections** é uma ferramenta web desenvolvida em Python/Streamlit que automatiza a organização e categorização de prompts para geração de imagens com Stable Diffusion no ComfyUI.

O problema que resolve: prompts de Stable Diffusion costumam ser longas strings com elementos misturados (estilo artístico, qualidade, personagem, poses, cenário), dificultando a reutilização e modificação de componentes específicos. Esta ferramenta separa automaticamente esses elementos em categorias bem definidas.

---

## 🎯 Problema Resolvido

### Antes (Prompt desorganizado):
```
1girl, solo, blush, ((Zero Two from Darling in the Franxx)), bikini, masterpiece, best quality, tsinne, 3d, blurry background, beach, arm up, bare legs, black choker, breasts, brown hair
```

### Depois (Prompt categorizado):
```
Estilo: tsinne, 3d

Qualidade: masterpiece, best quality

Background: ((simple background))

Personagem: 1girl, solo, Zero Two from Darling in the Franxx, brown hair

Restante: blush, bikini, arm up, bare legs, black choker, breasts
```

---

## 🔧 Funcionalidades

### 1. **Detecção Automática de Estilo Artístico**
- Identifica padrões do tipo: `autor, autor_style`
- Exemplos válidos:
  - `melkor, melkor_bt_style`
  - `reiq, reinaldo quintero style`
  - `kogeikun, kogeikun style`
  - `tsinne, 3d`

**Algoritmo**: Busca tags consecutivas onde a segunda contém "style" e inclui o nome do autor da primeira tag.

---

### 2. **Classificação de Qualidade**
Lista predefinida de termos que indicam qualidade/resolução da imagem:
- `masterpiece`
- `best quality`
- `rating_explicit`
- `nsfw`
- `amazing quality`
- `very aesthetic`
- `absurdres`
- `ultra detailed`
- `highres`
- `intricate details`
- `highly detailed`

---

### 3. **Normalização de Background**
- **Detecta** qualquer elemento de cenário nos prompts
- **Substitui automaticamente** por `((simple background))`

**Termos detectados:**
- Palavras com "background"
- Ambientes: `indoors`, `outdoors`, `tavern`, `beach`, `forest`, `city`, `room`, etc.
- Elementos de cena: `tables`, `sky`, `sunset`, `mountains`, `ocean`, etc.

**Por que?** Padroniza o background, facilitando substituição manual posterior se necessário.

---

### 4. **Separação Inteligente: Personagem vs Ações/Roupas**

#### **Vai para "Personagem":**
- Identificadores: `1girl`, `2girls`, `solo`, `1boy`, etc.
- Personagens nomeados: `Zero Two from Darling in the Franxx`, `momo ayase from DanDaDan`
- Descrições genéricas: `medieval barmaid`, `office lady`
- **Características físicas permanentes:**
  - Cabelo: `orange hair`, `long hair`, `hair over one eye`
  - Olhos: `blue eyes`, `heterochromia`
  - Corpo: `body type`, `skin tone`
  - Ornamentos naturais: `shamrock hair ornament`, `tattoo`, `scar`, `elf ears`, `tail`, `wings`

#### **Vai para "Restante do Prompt":**
- **Ações e poses:** `arm up`, `standing`, `sitting`, `looking at viewer`, `serving beer mugs`
- **Expressões:** `smile`, `blush`, `:o`, `seductive smile`
- **Roupas removíveis:** `bikini`, `shirt`, `corset`, `choker`, `jacket`, `boots`
- **Partes do corpo expostas:** `bare legs`, `navel`, `collarbone`, `armpit`
- **Enquadramentos:** `cowboy shot`, `full body`, `close-up`
- **Estados temporários:** `wet`, `shiny`, `see-through`

---

## 🧠 Lógica de Classificação

### Fluxo de Processamento:
```
1. Split do prompt por vírgulas
2. Iteração sequencial pelos tags
3. Para cada tag:
   ├─ É estilo? (autor + autor_style) → Categoria "Estilo"
   ├─ É qualidade? (match com lista) → Categoria "Qualidade"
   ├─ É background? (match com lista) → Sinaliza para substituir
   ├─ É identificador de personagem? → Categoria "Personagem" + ativa modo "seção personagem"
   ├─ Está em "seção personagem"?
   │  ├─ É trait físico? → Categoria "Personagem"
   │  └─ É ação/roupa? → Categoria "Restante" + desativa "seção personagem"
   └─ Fallback → Categoria "Restante"
```

### Heurísticas Aplicadas:
- **Tags consecutivas após identificadores de personagem** são analisadas quanto a serem características permanentes ou temporárias
- **Descrições curtas (≤3 palavras) sem termos de ação** na seção de personagem são classificadas como parte da descrição do personagem
- **Primeira detecção de ação/roupa** encerra a seção de personagem

---

## 📊 Exemplos Práticos

### Exemplo 1: Personagem de Anime com Estilo
**Entrada:**
```
melkor, melkor_bt_style, masterpiece, best quality, rating_explicit, nsfw, 
((simple background)), 1girl, momo ayase from DanDaDan, :o, arm up, bare legs, 
black choker, breasts, brown hair
```

**Saída:**
```
Estilo: melkor, melkor_bt_style

Qualidade: masterpiece, best quality, rating_explicit, nsfw

Background: ((simple background))

Personagem: 1girl, momo ayase from DanDaDan, brown hair, breasts

Restante: :o, arm up, bare legs, black choker
```

---

### Exemplo 2: Medieval Barmaid
**Entrada:**
```
1girl, medieval barmaid, orange hair, long hair, hair over one eye, shamrock, 
shamrock hair ornament, masterpiece, best quality, absurdres, Irish barmaid, 
green barmaid, corset, bodice, cross-laced corset, square neckline, 
detached collar, indoors, tavern, tables, solo, serving beer mugs, intricate, 
highly detailed
```

**Saída:**
```
Qualidade: masterpiece, best quality, absurdres, intricate, highly detailed

Background: ((simple background))

Personagem: 1girl, medieval barmaid, orange hair, long hair, hair over one eye, 
shamrock, shamrock hair ornament, solo

Restante: Irish barmaid, green barmaid, corset, bodice, cross-laced corset, 
square neckline, detached collar, serving beer mugs
```

---

### Exemplo 3: Zero Two com Estilo 3D
**Entrada:**
```
1girl, solo, blush, ((Zero Two from Darling in the Franxx)), bikini, armpit crease, 
large breasts, toned, thick thighs, blurry background, beach, leotard, shiny clothes, 
navel, arm behind head, looking at viewer, seductive smile, head tilt, skindentation, 
highleg leotard with flames on it, perfect tanline, red hair, beauty eyes, earrings, 
masterpiece, best quality, tsinne, 3d
```

**Saída:**
```
Estilo: tsinne, 3d

Qualidade: masterpiece, best quality

Background: ((simple background))

Personagem: 1girl, solo, Zero Two from Darling in the Franxx, large breasts, 
thick thighs, red hair, beauty eyes

Restante: blush, bikini, armpit crease, toned, leotard, shiny clothes, navel, 
arm behind head, looking at viewer, seductive smile, head tilt, skindentation, 
highleg leotard with flames on it, perfect tanline, earrings
```

---

## 🚀 Como Usar

### 1. Instalação
```bash
# Criar ambiente virtual (SEMPRE!)
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# ou
source venv/bin/activate     # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar
```bash
streamlit run app.py
```

### 3. Interface
1. Cole seu prompt na área de texto à esquerda
2. Clique em "🔄 Processar Prompt"
3. Visualize as categorias separadas à direita
4. Copie o prompt reorganizado da área de saída

---

## 🎨 Interface do Usuário

### Layout em 2 Colunas:
- **Coluna Esquerda:** Input do prompt original
- **Coluna Direita:** 
  - Categorias expandíveis com ícones
  - Prompt formatado final para copiar

### Categorias Visuais:
- 🎨 **Estilo**
- ⭐ **Qualidade**
- 🖼️ **Background**
- 👤 **Personagem**
- 📝 **Restante do Prompt**

---

## 🔮 Melhorias Futuras

### Em Roadmap:
- [ ] **Integração com LLM** para detecção semântica de backgrounds complexos
- [ ] **Edição manual de categorias** na interface
- [ ] **Histórico de prompts** processados com salvamento local
- [ ] **Export/Import** em múltiplos formatos (JSON, TXT, CSV)
- [ ] **Listas expansíveis** via interface (adicionar termos de qualidade, estilos, etc.)
- [ ] **Templates predefinidos** por estilo artístico
- [ ] **Validação de sintaxe** ComfyUI (parênteses balanceados, pesos, etc.)
- [ ] **Geração de variações** combinatórias de prompts

### Limitações Conhecidas:
- **Termos ambíguos:** Palavras como "perfect", "toned" podem ser classificadas incorretamente
- **Estilos não-padrão:** Estilos que não seguem o padrão `autor, autor_style` não são detectados
- **Contexto semântico:** Não entende nuances (ex: "green barmaid" é cor de roupa ou raça?)

---

## 🛠️ Tecnologias

- **Python 3.12+**
- **Streamlit 1.28+** - Framework web para apps de dados
- **Regex** - Processamento de padrões textuais

---

## 📝 Estrutura do Projeto

```
promptsections/
├── app.py              # Aplicação principal Streamlit
├── requirements.txt    # Dependências Python
├── README.md          # Este arquivo
└── venv/              # Ambiente virtual (não versionado)
```

---

## 🧪 Casos de Teste

Para validar a ferramenta, teste com:

1. **Prompt mínimo:** `1girl, masterpiece`
2. **Prompt com estilo:** `melkor, melkor_style, 1girl, best quality`
3. **Prompt complexo:** Exemplo do Medieval Barmaid acima
4. **Prompt sem background:** Deve manter Background vazio
5. **Prompt sem estilo:** Deve manter Estilo vazio
6. **Tags duplicadas:** Comportamento atual preserva duplicatas

---

## 🤝 Contribuindo

### Como reportar problemas:
1. Identifique o prompt que gerou resultado incorreto
2. Especifique qual categoria está errada
3. Explique o resultado esperado
4. Forneça contexto (se é padrão comum no ComfyUI)

### Adicionando novos termos:
Edite as listas em `app.py`:
- `QUALITY_TERMS` - Termos de qualidade
- `BACKGROUND_KEYWORDS` - Palavras-chave de cenário
- `CHARACTER_IDENTIFIERS` - Identificadores de personagem
- `PHYSICAL_TRAITS` - Características físicas
- `ACTION_CLOTHING_KEYWORDS` - Ações e roupas

---

## 📄 Licença

Este projeto é de código aberto. Use, modifique e distribua livremente.

---

## 🎓 Conceitos de Stable Diffusion

### Por que separar prompts?
1. **Reutilização:** Trocar apenas o personagem mantendo estilo/qualidade
2. **Experimentação:** Testar diferentes combinações de forma sistemática
3. **Organização:** Manter biblioteca de prompts modular
4. **Debugging:** Identificar qual componente afeta negativamente a imagem

### Ordem importa?
**Sim!** No Stable Diffusion, termos no início do prompt têm mais peso. A ordem padrão desta ferramenta é:
1. Estilo (define renderização geral)
2. Qualidade (afeta resolução/detalhamento)
3. Background (contexto da cena)
4. Personagem (sujeito principal)
5. Detalhes (refinamentos)

---

## 💡 Dicas de Uso

1. **Sempre revise a categorização** - A ferramenta usa heurísticas, não IA semântica
2. **Use backgrounds genéricos** - `((simple background))` facilita variações posteriores
3. **Personalize as listas** - Adicione estilos/termos específicos do seu workflow
4. **Combine com negative prompts** - Esta ferramenta foca em prompts positivos
5. **Teste variações** - Gere múltiplas versões trocando apenas uma categoria

---

**Desenvolvido para otimizar workflows de geração de imagens com Stable Diffusion/ComfyUI**
