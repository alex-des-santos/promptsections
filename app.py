import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st


def load_prompt_config(config_path: Path) -> Dict[str, List[str]]:
    """Carrega listas de classificação a partir de um arquivo JSON."""
    with config_path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    required_keys = [
        "quality_terms",
        "background_keywords",
        "character_identifiers",
        "physical_traits",
        "action_clothing_keywords",
        "clothing_keywords",
        "pose_keywords",
    ]

    for key in required_keys:
        data.setdefault(key, [])

    return data


CONFIG_PATH = Path(__file__).with_name("prompt_config.json")
PROMPT_CONFIG = load_prompt_config(CONFIG_PATH)

# Diretórios para regras customizadas (compatível com Streamlit Cloud)
DEFAULT_CUSTOM_RULES_PATH = Path(__file__).with_name("custom_rules.json")
DATA_DIR = Path(
    os.environ.get("PROMPT_SECTIONS_DATA_DIR", Path(tempfile.gettempdir()) / "prompt_sections")
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CUSTOM_RULES_STORAGE_PATH = Path(
    os.environ.get("PROMPT_SECTIONS_RULES_PATH", DATA_DIR / "custom_rules.json")
)


def load_custom_rules(path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Carrega regras customizadas e retorna (raw, normalizado)."""
    if not path.exists():
        return {}, {}

    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}, {}

    if not isinstance(data, dict):
        return {}, {}

    return normalize_rules_dict(data)


def normalize_rules_dict(data: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    raw_rules: Dict[str, str] = {}
    normalized_rules: Dict[str, str] = {}

    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        key_clean = key.strip()
        category_clean = value.strip()
        if not key_clean or not category_clean:
            continue
        raw_rules[key_clean] = category_clean
        normalized_rules[key_clean.lower()] = category_clean

    return raw_rules, normalized_rules


def save_custom_rules(path: Path, rules: Dict[str, str]) -> bool:
    serialized = json.dumps(rules, indent=2, ensure_ascii=False)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
        return True
    except OSError:
        return False


def update_custom_rules(raw_rules: Dict[str, str]) -> None:
    global CUSTOM_RULES_RAW, CUSTOM_RULES
    CUSTOM_RULES_RAW = dict(sorted(raw_rules.items()))
    CUSTOM_RULES = {key.lower(): value for key, value in CUSTOM_RULES_RAW.items()}


INITIAL_RULES_PATH = (
    CUSTOM_RULES_STORAGE_PATH if CUSTOM_RULES_STORAGE_PATH.exists() else DEFAULT_CUSTOM_RULES_PATH
)
CUSTOM_RULES_RAW, CUSTOM_RULES = load_custom_rules(INITIAL_RULES_PATH)


def set_custom_rule(tag: str, category: str) -> None:
    """Atualiza uma regra customizada e persiste no disco."""
    tag_key = tag.strip()
    if not tag_key:
        return

    category_value = category.strip() or "Restante do Prompt"

    new_rules = dict(CUSTOM_RULES_RAW)
    new_rules[tag_key] = category_value
    update_custom_rules(new_rules)
    persisted = save_custom_rules(CUSTOM_RULES_STORAGE_PATH, CUSTOM_RULES_RAW)
    if not persisted:
        cache_rules_in_session(CUSTOM_RULES_RAW)


def delete_custom_rule(tag: str) -> None:
    """Remove uma regra customizada."""
    tag_key = tag.strip()
    if not tag_key:
        return

    if tag_key in CUSTOM_RULES_RAW:
        new_rules = dict(CUSTOM_RULES_RAW)
        del new_rules[tag_key]
        update_custom_rules(new_rules)
        persisted = save_custom_rules(CUSTOM_RULES_STORAGE_PATH, CUSTOM_RULES_RAW)
        if not persisted:
            cache_rules_in_session(CUSTOM_RULES_RAW)

# Prompt padrão exibido ao abrir o app
DEFAULT_PROMPT = (
    "1girl, solo, blush, ((Zero Two from Darling in the Franxx)), bikini, masterpiece, "
    "best quality, tsinne, 3d, blurry background, beach"
)

# Listas de termos predefinidos carregadas do JSON
QUALITY_TERMS = PROMPT_CONFIG["quality_terms"]
BACKGROUND_KEYWORDS = PROMPT_CONFIG["background_keywords"]
CHARACTER_IDENTIFIERS = PROMPT_CONFIG["character_identifiers"]
PHYSICAL_TRAITS = PROMPT_CONFIG["physical_traits"]
ACTION_CLOTHING_KEYWORDS = PROMPT_CONFIG["action_clothing_keywords"]
CLOTHING_KEYWORDS = PROMPT_CONFIG["clothing_keywords"]
POSE_KEYWORDS = PROMPT_CONFIG["pose_keywords"]

QUALITY_TERMS_LOWER = tuple(term.lower() for term in QUALITY_TERMS)
BACKGROUND_KEYWORDS_LOWER = tuple(term.lower() for term in BACKGROUND_KEYWORDS)
CHARACTER_IDENTIFIERS_SET = {identifier.lower() for identifier in CHARACTER_IDENTIFIERS}
PHYSICAL_TRAITS_LOWER = tuple(trait.lower() for trait in PHYSICAL_TRAITS)
ACTION_CLOTHING_KEYWORDS_LOWER = tuple(
    keyword.lower() for keyword in ACTION_CLOTHING_KEYWORDS
)
CLOTHING_KEYWORDS_LOWER = tuple(keyword.lower() for keyword in CLOTHING_KEYWORDS)
POSE_KEYWORDS_LOWER = tuple(keyword.lower() for keyword in POSE_KEYWORDS)

CATEGORY_OPTIONS = [
    "Estilo",
    "Qualidade",
    "Background",
    "Personagem",
    "Pose",
    "Roupas",
    "Restante do Prompt",
]


def detect_style(tags: List[str], index: int) -> tuple[bool, int]:
    """
    Detecta se o tag atual é parte de um padrão de estilo.
    Padrão: autor, autor_style ou autor, autor estilo style
    Retorna (is_style, próximo_index)
    """
    if index >= len(tags) - 1:
        return False, index + 1
    
    current_tag = tags[index].lower().strip()
    next_tag = tags[index + 1].lower().strip()
    
    # Verificar se próximo tag contém 'style'
    if 'style' not in next_tag:
        return False, index + 1
    
    # Extrair palavras do nome do autor
    author_words = current_tag.replace('_', ' ').replace('-', ' ').split()
    
    # Verificar se alguma palavra do autor aparece no próximo tag
    for word in author_words:
        if len(word) > 2 and word in next_tag:  # Palavras com mais de 2 letras
            return True, index + 2
    
    return False, index + 1


def is_physical_trait(tag: str) -> bool:
    """Verifica se o tag é uma característica física permanente."""
    tag_lower = tag.lower()
    return any(trait in tag_lower for trait in PHYSICAL_TRAITS_LOWER)


def is_action_or_clothing(tag: str) -> bool:
    """Verifica se o tag é uma ação ou pose."""
    tag_lower = tag.lower()
    return any(keyword in tag_lower for keyword in ACTION_CLOTHING_KEYWORDS_LOWER)


def is_clothing_tag(tag: str) -> bool:
    """Verifica se o tag descreve uma peça de roupa."""
    tag_lower = tag.lower()
    return any(keyword in tag_lower for keyword in CLOTHING_KEYWORDS_LOWER)


def is_pose_tag(tag: str) -> bool:
    """Verifica se o tag descreve pose/enquadramento."""
    tag_lower = tag.lower()
    return any(keyword in tag_lower for keyword in POSE_KEYWORDS_LOWER)


def normalize_tag(tag: str) -> str:
    """Remove ênfases simples do tipo (tag:1.2) mantendo apenas a tag."""
    stripped = tag.strip()
    if len(stripped) < 5:
        return stripped
    if stripped.startswith("(") and stripped.endswith(")"):
        inner = stripped[1:-1]
        if ":" in inner and inner.count(":") == 1:
            candidate, weight = inner.split(":")
            candidate = candidate.strip()
            weight = weight.strip()
            if candidate and weight.replace(".", "", 1).isdigit():
                return candidate
    return stripped


def parse_prompt(prompt: str) -> tuple[Dict[str, List[str]], List[Dict[str, str]]]:
    """
    Parseia o prompt e separa em categorias.
    """
    # Limpar e separar por vírgulas
    tags = [tag.strip() for tag in prompt.split(',') if tag.strip()]
    
    style_tags = []
    quality_tags = []
    background_detected = False
    character_tags = []
    clothing_tags = []
    pose_tags = []
    rest_tags = []
    
    classification_details: List[Dict[str, str]] = []

    def record(tag_value: str, category: str, reason: str) -> None:
        classification_details.append(
            {
                "tag": tag_value,
                "categoria": category,
                "motivo": reason,
            }
        )

    i = 0
    in_character_section = False
    
    custom_rules = CUSTOM_RULES

    while i < len(tags):
        tag_raw = tags[i]
        tag = normalize_tag(tag_raw)
        tag_lower = tag.lower()
        
        # 1. Detectar ESTILO (autor + autor_style)
        is_style, next_i = detect_style(tags, i)
        if is_style:
            author_tag = normalize_tag(tags[i])
            style_tag = normalize_tag(tags[i + 1])
            style_tags.append(author_tag)
            style_tags.append(style_tag)
            record(author_tag, "Estilo", "Autor detectado em sequência de estilo")
            record(style_tag, "Estilo", "Tag identificada como estilo")
            i = next_i
            continue
        
        # 2. Detectar QUALIDADE
        matched_quality = next(
            (quality_term for quality_term in QUALITY_TERMS_LOWER if quality_term in tag_lower),
            None,
        )
        if matched_quality:
            quality_tags.append(tag)
            record(tag, "Qualidade", f"Indicador de qualidade ({matched_quality})")
            i += 1
            continue
        
        # 3. Detectar BACKGROUND
        matched_background = next(
            (bg_keyword for bg_keyword in BACKGROUND_KEYWORDS_LOWER if bg_keyword in tag_lower),
            None,
        )
        if matched_background:
            background_detected = True
            record(tag, "Background", f"Cenário detectado ({matched_background})")
            i += 1
            continue
        
        # 4. Detectar início de seção PERSONAGEM
        if tag_lower in CHARACTER_IDENTIFIERS_SET:
            character_tags.append(tag)
            in_character_section = True
            record(tag, "Personagem", "Identificador de personagem")
            i += 1
            continue
        
        # 5. Detectar personagem nomeado (padrão "from [série]")
        if ' from ' in tag:
            character_tags.append(tag)
            in_character_section = True
            record(tag, "Personagem", "Personagem nomeado detectado")
            i += 1
            continue
        
        # 6. Se estamos na seção de personagem, classificar entre físico e ação/roupa
        if in_character_section:
            # Características físicas vão para PERSONAGEM
            if is_physical_trait(tag):
                character_tags.append(tag)
                record(tag, "Personagem", "Característica física permanente")
                i += 1
                continue
            
            # Itens de roupa vão para ROUPAS e encerram a seção
            if is_clothing_tag(tag):
                clothing_tags.append(tag)
                record(tag, "Roupas", "Item de vestuário detectado")
                in_character_section = False
                i += 1
                continue

            # Poses vão para POSE e encerram a seção
            if is_pose_tag(tag):
                pose_tags.append(tag)
                record(tag, "Pose", "Pose detectada")
                in_character_section = False
                i += 1
                continue

            # Ações terminam a seção de personagem
            if is_action_or_clothing(tag):
                in_character_section = False
                rest_tags.append(tag)
                record(tag, "Restante do Prompt", "Ação/pose detectada")
                i += 1
                continue
            
            # Tags genéricas na seção de personagem (ex: "medieval barmaid")
            # Heurística: descrições curtas sem termos de ação vão para personagem
            if len(tag.split()) <= 3 and not any(char.isdigit() for char in tag):
                character_tags.append(tag)
                record(tag, "Personagem", "Descrição curta atribuída ao personagem")
                i += 1
                continue

        # 6.5 Regras customizadas definidas pelo usuário
        custom_category = custom_rules.get(tag_lower)
        if custom_category:
            normalized_category = custom_category.strip()
            if normalized_category == "Background":
                background_detected = True
            elif normalized_category == "Estilo":
                style_tags.append(tag)
            elif normalized_category == "Qualidade":
                quality_tags.append(tag)
            elif normalized_category == "Personagem":
                character_tags.append(tag)
                in_character_section = True
            elif normalized_category == "Pose":
                pose_tags.append(tag)
                in_character_section = False
            elif normalized_category == "Roupas":
                clothing_tags.append(tag)
            else:
                normalized_category = "Restante do Prompt"
                rest_tags.append(tag)

            record(tag, normalized_category, "Regra customizada")
            i += 1
            continue

        # 6.6 Itens de roupa fora da seção de personagem
        if is_clothing_tag(tag):
            clothing_tags.append(tag)
            record(tag, "Roupas", "Item de vestuário detectado")
            in_character_section = False
            i += 1
            continue

        # 6.7 Poses fora da seção
        if is_pose_tag(tag):
            pose_tags.append(tag)
            record(tag, "Pose", "Pose detectada")
            in_character_section = False
            i += 1
            continue
        
        # 7. Tudo que não se encaixou vai para RESTANTE
        rest_tags.append(tag)
        record(tag, "Restante do Prompt", "Sem regra aplicada")
        i += 1
    
    categorized = {
        'Estilo': style_tags,
        'Qualidade': quality_tags,
        'Background': ['((simple background))'] if background_detected else [],
        'Personagem': character_tags,
        'Pose': pose_tags,
        'Roupas': clothing_tags,
        'Restante do Prompt': rest_tags
    }
    
    return categorized, classification_details


def format_output(categorized: Dict[str, List[str]]) -> str:
    """
    Formata a saída no formato esperado.
    """
    output_parts: List[str] = []
    ordered_sections = [
        "Estilo",
        "Qualidade",
        "Background",
        "Personagem",
        "Pose",
        "Roupas",
        "Restante do Prompt",
    ]

    for section in ordered_sections:
        content = categorized.get(section, [])
        if content:
            output_parts.append(', '.join(content))

    return "\n\n".join(output_parts)


def render_copy_prompt(text: str) -> None:
    """Renderiza um botão de copiar com fallback para navegadores sem suporte."""
    if not text:
        return

    if hasattr(st, "clipboard"):
        st.clipboard(text, label="Copiar prompt formatado")
    else:
        copied = st.button("Copiar prompt formatado", use_container_width=True)
        if copied:
            st.toast("Selecione o prompt acima e copie manualmente (Ctrl+C).")


def render_classification_table(details: List[Dict[str, str]]) -> None:
    """Exibe uma tabela simples com o detalhamento das tags classificadas."""
    if not details:
        return

    def escape(value: str) -> str:
        return value.replace("|", "\\|")

    rows = [
        "| Tag | Categoria | Motivo |",
        "| --- | --- | --- |",
    ]
    for item in details:
        rows.append(
            f"| {escape(item['tag'])} | {escape(item['categoria'])} | {escape(item['motivo'])} |"
        )

    st.markdown("\n".join(rows))


def main():
    st.set_page_config(
        page_title="Prompt Sections - Stable Diffusion",
        page_icon="🎨",
        layout="wide"
    )

    if 'custom_rules_runtime' in st.session_state:
        update_custom_rules(st.session_state['custom_rules_runtime'])
    
    st.title("🎨 Prompt Sections para Stable Diffusion")
    st.markdown("Separe e organize seus prompts em categorias estruturadas.")
    
    if 'prompt_input' not in st.session_state:
        st.session_state['prompt_input'] = DEFAULT_PROMPT

    # Área de input
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Prompt Original")
        prompt_input = st.text_area(
            "Cole seu prompt aqui:",
            value=st.session_state['prompt_input'],
            height=400,
            key="prompt_input",
            placeholder="1girl, solo, blush, ((Zero Two from Darling in the Franxx)), bikini, masterpiece, best quality..."
        )
        
        if st.button("🔄 Processar Prompt", type="primary", use_container_width=True):
            if prompt_input.strip():
                categorized, trace = parse_prompt(prompt_input)
                st.session_state['categorized'] = categorized
                st.session_state['classification_trace'] = trace
                st.session_state['formatted_output'] = format_output(categorized)
            else:
                st.warning("⚠️ Por favor, insira um prompt válido.")
    
    with col2:
        st.subheader("✨ Resultado Categorizado")
        
        if 'categorized' in st.session_state:
            categorized = st.session_state['categorized']
            trace = st.session_state.get('classification_trace', [])
            
            # Exibir cada categoria
            categories_display = {
                'Estilo': '🎨',
                'Qualidade': '⭐',
                'Background': '🖼️',
                'Personagem': '👤',
                'Pose': '🧘',
                'Roupas': '👗',
                'Restante do Prompt': '📝'
            }

            unmatched_tags: List[str] = []
            for item in trace:
                if item['categoria'] == 'Restante do Prompt' and item['motivo'] == 'Sem regra aplicada':
                    if item['tag'] not in unmatched_tags:
                        unmatched_tags.append(item['tag'])
            
            for category, icon in categories_display.items():
                content = categorized[category]
                if content:
                    with st.expander(f"{icon} **{category}**", expanded=True):
                        st.code(', '.join(content), language=None)
                        if category == 'Restante do Prompt' and unmatched_tags:
                            st.warning(
                                "Sem regras específicas para: " + ', '.join(unmatched_tags),
                                icon="ℹ️"
                            )
            
            if unmatched_tags:
                with st.expander("⚙️ Definir regras para tags sem categoria"):
                    st.markdown(
                        "Associe uma tag a uma categoria para que futuras análises sejam automáticas."
                    )
                    with st.form("custom_rule_form", clear_on_submit=True):
                        tag_choice = st.selectbox(
                            "Tag",
                            unmatched_tags,
                            key="custom_rule_tag"
                        )
                        category_choice = st.selectbox(
                            "Categoria",
                            CATEGORY_OPTIONS,
                            index=len(CATEGORY_OPTIONS) - 1,
                            key="custom_rule_category"
                        )
                        submitted = st.form_submit_button("Salvar regra")
                    
                    if submitted:
                        set_custom_rule(tag_choice, category_choice)
                        st.success(f"Regra salva: {tag_choice} → {category_choice}")
                        current_prompt = st.session_state.get('prompt_input', '')
                        if current_prompt:
                            categorized, trace = parse_prompt(current_prompt)
                            st.session_state['categorized'] = categorized
                            st.session_state['classification_trace'] = trace
                            st.session_state['formatted_output'] = format_output(categorized)
                            st.rerun()

            with st.expander("🗂️ Gerenciar regras customizadas", expanded=False):
                if CUSTOM_RULES_STORAGE_PATH.exists():
                    st.caption(f"Regras persistidas em: {CUSTOM_RULES_STORAGE_PATH}")
                else:
                    st.caption(
                        "Usando regras padrão do repositório. Ao salvar, criaremos um arquivo temporário compatível com Streamlit Cloud."
                    )

                custom_rules_items = sorted(CUSTOM_RULES_RAW.items())
                if custom_rules_items:
                    st.table(
                        {
                            "Tag": [tag for tag, _ in custom_rules_items],
                            "Categoria": [category for _, category in custom_rules_items],
                        }
                    )
                else:
                    st.info("Nenhuma regra cadastrada ainda.")

                download_data = json.dumps(
                    CUSTOM_RULES_RAW, indent=2, ensure_ascii=False
                ).encode("utf-8")
                st.download_button(
                    "Baixar JSON de regras",
                    data=download_data,
                    file_name="custom_rules.json",
                    mime="application/json",
                    use_container_width=True,
                )

                with st.form("import_rules_form"):
                    uploaded_file = st.file_uploader(
                        "Importar regras (JSON)", type=["json"], key="import_rules_file"
                    )
                    import_submit = st.form_submit_button("Importar arquivo")

                if import_submit:
                    if uploaded_file is None:
                        st.warning("Selecione um arquivo para importar.")
                    else:
                        try:
                            uploaded_data = json.load(uploaded_file)
                        except json.JSONDecodeError:
                            st.error("Arquivo JSON inválido.")
                        else:
                            if not isinstance(uploaded_data, dict):
                                st.error("O JSON deve ser um objeto simples com pares tag/categoria.")
                            else:
                                raw_rules, _ = normalize_rules_dict(uploaded_data)
                                if not raw_rules:
                                    st.warning("Nenhuma regra válida encontrada no arquivo.")
                                else:
                                    update_custom_rules(raw_rules)
                                    persisted = save_custom_rules(
                                        CUSTOM_RULES_STORAGE_PATH, CUSTOM_RULES_RAW
                                    )
                                    if not persisted:
                                        cache_rules_in_session(CUSTOM_RULES_RAW)
                                    st.success("Regras importadas com sucesso.")
                                    st.rerun()

                st.markdown("### Adicionar regra manualmente")
                with st.form("manual_rule_form", clear_on_submit=True):
                    manual_tag = st.text_input("Tag exata (case-insensitive)")
                    manual_category = st.selectbox(
                        "Categoria",
                        CATEGORY_OPTIONS,
                        index=len(CATEGORY_OPTIONS) - 1,
                        key="manual_rule_category"
                    )
                    submitted_manual = st.form_submit_button("Salvar nova regra")

                if submitted_manual and manual_tag.strip():
                    set_custom_rule(manual_tag, manual_category)
                    st.success(f"Regra salva: {manual_tag.strip()} → {manual_category}")
                    current_prompt = st.session_state.get('prompt_input', '')
                    if current_prompt:
                        categorized, trace = parse_prompt(current_prompt)
                        st.session_state['categorized'] = categorized
                        st.session_state['classification_trace'] = trace
                        st.session_state['formatted_output'] = format_output(categorized)
                    st.rerun()

                if custom_rules_items:
                    st.markdown("### Remover regra")
                    with st.form("delete_rule_form"):
                        delete_choice = st.selectbox(
                            "Selecione a regra para remover",
                            [tag for tag, _ in custom_rules_items],
                            key="delete_rule_choice"
                        )
                        delete_submit = st.form_submit_button("Remover regra")

                    if delete_submit:
                        delete_custom_rule(delete_choice)
                        st.warning(f"Regra removida: {delete_choice}")
                        current_prompt = st.session_state.get('prompt_input', '')
                        if current_prompt:
                            categorized, trace = parse_prompt(current_prompt)
                            st.session_state['categorized'] = categorized
                            st.session_state['classification_trace'] = trace
                            st.session_state['formatted_output'] = format_output(categorized)
                        st.rerun()
            
            if trace:
                trace_tag_map: Dict[str, str] = {}
                for item in trace:
                    trace_tag_map.setdefault(item['tag'], item['categoria'])

                with st.expander("🔄 Reclassificar tags existentes", expanded=False):
                    st.markdown(
                        "Escolha qualquer tag já classificada e mova para outra categoria. "
                        "Isso cria/atualiza uma regra customizada automaticamente."
                    )
                    if trace_tag_map:
                        with st.form("reclassify_form"):
                            tag_choice = st.selectbox(
                                "Tag",
                                options=list(trace_tag_map.keys()),
                                format_func=lambda value: f"{value} (atual: {trace_tag_map[value]})",
                                key="reclassify_tag",
                            )
                            current_category = trace_tag_map.get(tag_choice, "Restante do Prompt")
                            default_index = (
                                CATEGORY_OPTIONS.index(current_category)
                                if current_category in CATEGORY_OPTIONS
                                else len(CATEGORY_OPTIONS) - 1
                            )
                            new_category = st.selectbox(
                                "Nova categoria",
                                CATEGORY_OPTIONS,
                                index=default_index,
                                key="reclassify_category",
                            )
                            submit_reclass = st.form_submit_button("Reclassificar")

                        if submit_reclass and tag_choice:
                            set_custom_rule(tag_choice, new_category)
                            st.success(f"{tag_choice} movido para {new_category}.")
                            current_prompt = st.session_state.get('prompt_input', '')
                            if current_prompt:
                                categorized, trace = parse_prompt(current_prompt)
                                st.session_state['categorized'] = categorized
                                st.session_state['classification_trace'] = trace
                                st.session_state['formatted_output'] = format_output(categorized)
                            st.rerun()
                    else:
                        st.info("Nenhuma tag disponível para reclassificar.")

                st.subheader("🧠 Detalhamento das tags analisadas")
                render_classification_table(trace)
            
            st.divider()
            
            # Saída formatada final
            st.subheader("📋 Prompt Formatado")
            formatted = format_output(categorized)
            st.session_state['formatted_output'] = formatted
            st.text_area(
                "Copie o prompt reorganizado:",
                value=formatted,
                height=300,
                key="output"
            )
            render_copy_prompt(formatted)
        else:
            st.info("👈 Cole um prompt e clique em 'Processar Prompt' para ver os resultados.")
    
    # Rodapé com exemplos
    with st.expander("📚 Ver Exemplos de Prompts"):
        st.markdown("""
        ### Exemplo 1: Personagem de Anime
        **Entrada:**
        ```
        melkor, melkor_bt_style, masterpiece, best quality, rating_explicit, nsfw, 
        ((simple background)), 1girl, momo ayase from DanDaDan, :o, arm up, bare legs
        ```
        
        ### Exemplo 2: Zero Two
        **Entrada:**
        ```
        1girl, solo, blush, ((Zero Two from Darling in the Franxx)), bikini, 
        masterpiece, best quality, tsinne, 3d, blurry background, beach
        ```
        
        ### Exemplo 3: Medieval Barmaid
        **Entrada:**
        ```
        1girl, medieval barmaid, orange hair, long hair, hair over one eye, shamrock, 
        shamrock hair ornament, masterpiece, best quality, absurdres, indoors, tavern, 
        solo, serving beer mugs
        ```
        """)


if __name__ == "__main__":
    main()
CUSTOM_RULES_RAW, CUSTOM_RULES = load_custom_rules(INITIAL_RULES_PATH)


def cache_rules_in_session(raw_rules: Dict[str, str]) -> None:
    """Guarda regras em memória para ambientes somente leitura."""
    try:
        st.session_state['custom_rules_runtime'] = dict(raw_rules)
    except Exception:
        pass
