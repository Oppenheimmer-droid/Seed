"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    WIDGETS DE ENTRADA                                    ║
║          Utilidades de input con validación para el menú                 ║
║          Puro Python 3.13 - Sin dependencias externas                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Widgets disponibles:
- input_string(): Input básico con validación
- input_number(): Input numérico (int o float)
- input_yes_no(): Input boolean (s/n)
- input_address(): Input de dirección Solana
- input_menu(): Selector de opciones numeradas
- input_float_range(): Input float con rango
- clear_screen(): Limpia la terminal
- print_header(): Imprime header con estilo
- print_table(): Imprime tabla formateada
"""

import os
import sys
from typing import Any, Callable, List, Optional, Tuple, Union

# ============================================
# CONSTANTES DE ESTILO
# ============================================

COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "bg_red": "\033[41m",
    "bg_green": "\033[42m",
    "bg_yellow": "\033[43m",
    "bg_blue": "\033[44m",
}

# Detectar si terminal soporta colores
USE_COLORS = sys.stdout.isatty() and os.getenv("TERM") != "dumb"


def _color(text: str, color: str) -> str:
    """Aplica color al texto si está habilitado."""
    if USE_COLORS and color in COLORS:
        return f"{COLORS[color]}{text}{COLORS['reset']}"
    return text


def _bold(text: str) -> str:
    """Aplica negrita."""
    return _color(text, "bold")


def _red(text: str) -> str:
    return _color(text, "red")


def _green(text: str) -> str:
    return _color(text, "green")


def _yellow(text: str) -> str:
    return _color(text, "yellow")


def _cyan(text: str) -> str:
    return _color(text, "cyan")


# ============================================
# UTILIDADES DE PANTALLA
# ============================================

def clear_screen() -> None:
    """Limpia la pantalla de la terminal."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str, width: int = 60) -> None:
    """Imprime un header centrado con bordes."""
    print()
    print(_cyan("═" * width))
    print(_cyan("║") + _bold(f"  {title.center(width - 4)}") + _cyan("║"))
    print(_cyan("═" * width))


def print_footer(width: int = 60) -> None:
    """Imprime un footer con línea."""
    print(_cyan("═" * width))
    print()


def print_divider(char: str = "─", width: int = 60) -> None:
    """Imprime una línea divisoria."""
    print(_cyan(char * width))


def print_success(message: str) -> None:
    """Imprime mensaje de éxito."""
    print(f"{_green('✅')} {message}")


def print_error(message: str) -> None:
    """Imprime mensaje de error."""
    print(f"{_red('❌')} {message}")


def print_warning(message: str) -> None:
    """Imprime mensaje de advertencia."""
    print(f"{_yellow('⚠️')} {message}")


def print_info(message: str) -> None:
    """Imprime mensaje informativo."""
    print(f"{_cyan('ℹ️')} {message}")


def print_table(
    headers: List[str],
    rows: List[List[str]],
    max_width: int = 60,
) -> None:
    """Imprime una tabla formateada."""
    if not rows:
        print(_yellow("  (vacío)"))
        return
    
    # Calcular anchos de columna
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Asegurar que no exceda max_width
    total = sum(col_widths) + len(headers) * 3 + 1
    if total > max_width:
        scale = (max_width - len(headers) * 3 - 1) / sum(col_widths)
        col_widths = [max(10, int(w * scale)) for w in col_widths]
    
    # Imprimir headers
    header_line = "  │ "
    header_line += " │ ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    header_line += " │"
    print(_bold(header_line))
    print(_cyan("  ├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"))
    
    # Imprimir filas
    for row in rows:
        row_line = "  │ "
        row_line += " │ ".join(str(cell).ljust(col_widths[i])[:col_widths[i]] 
                              for i, cell in enumerate(row))
        row_line += " │"
        print(row_line)
    print()


def print_banner(text: str) -> None:
    """Imprime un banner simple."""
    clear_screen()
    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║                                                          ║",
    ]
    
    # Centrar texto
    for line in text.split("\n"):
        padding = (56 - len(line)) // 2
        lines.append(f"║{' ' * padding}{line}{' ' * (56 - padding - len(line))}║")
    
    lines.append("║                                                          ║")
    lines.append("╚══════════════════════════════════════════════════════════╝")
    
    for line in lines:
        print(_cyan(line))


# ============================================
# INPUTS CON VALIDACIÓN
# ============================================

def input_string(
    prompt: str,
    default: str = "",
    required: bool = False,
    validator: Optional[Callable[[str], bool]] = None,
    error_msg: str = "Entrada inválida",
) -> str:
    """
    Input básico con validación opcional.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto
        required: Si es obligatorio
        validator: Función que retorna True si es válido
        error_msg: Mensaje de error
        
    Returns:
        String validado
    """
    while True:
        if default:
            user_input = input(f"  {prompt} [{default}]: ").strip() or default
        else:
            user_input = input(f"  {prompt}: ").strip()
        
        if not user_input and required:
            print_error("Este campo es obligatorio")
            continue
        
        if validator and user_input and not validator(user_input):
            print_error(error_msg)
            continue
        
        return user_input


def input_number(
    prompt: str,
    default: Union[int, float, None] = None,
    num_type: type = float,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    required: bool = False,
) -> Union[int, float, None]:
    """
    Input numérico con validación de rango.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto
        num_type: int o float
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        required: Si es obligatorio
        
    Returns:
        Número validado o None si se cancela
    """
    while True:
        default_str = str(default) if default is not None else ""
        user_input = input(f"  {prompt}{f' [{default_str}]' if default_str else ''}: ").strip()
        
        if not user_input:
            if default is not None:
                return default
            if required:
                print_error("Este campo es obligatorio")
                continue
            return None
        
        # Aceptar tanto punto como coma para decimales
        user_input = user_input.replace(",", ".")
        
        try:
            value = num_type(user_input)
        except ValueError:
            print_error(f"'{user_input}' no es un número válido")
            continue
        
        if min_val is not None and value < min_val:
            print_error(f"El valor debe ser al menos {min_val}")
            continue
        
        if max_val is not None and value > max_val:
            print_error(f"El valor no puede exceder {max_val}")
            continue
        
        return value


def input_yes_no(
    prompt: str,
    default: Optional[bool] = None,
) -> Optional[bool]:
    """
    Input sí/no con validación.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto (None = obligatorio)
        
    Returns:
        True (sí), False (no), o None (vacío cuando no es obligatorio)
    """
    options = ""
    if default is True:
        options = " (S/n)"
    elif default is False:
        options = " (s/N)"
    
    while True:
        user_input = input(f"  {prompt}{options}: ").strip().lower()
        
        if not user_input:
            if default is not None:
                return default
            print_error("Por favor ingrese 's' o 'n'")
            continue
        
        if user_input in ("s", "si", "sí", "y", "yes"):
            return True
        elif user_input in ("n", "no"):
            return False
        else:
            print_error("Por favor ingrese 's' o 'n'")


def input_address(
    prompt: str,
    default: str = "",
) -> Optional[str]:
    """
    Input de dirección Solana con validación.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto
        
    Returns:
        Dirección validada o None
    """
    while True:
        if default:
            user_input = input(f"  {prompt} [{default[:12]}...]: ").strip() or default
        else:
            user_input = input(f"  {prompt}: ").strip()
        
        if not user_input:
            if default:
                return default
            print_error("La dirección no puede estar vacía")
            continue
        
        if not _validate_solana_address(user_input):
            print_error("Dirección inválida. Debe ser base58 de 32-44 caracteres")
            continue
        
        return user_input


def input_menu(
    options: List[str],
    prompt: str = "Seleccione una opción",
    allow_cancel: bool = True,
) -> Optional[int]:
    """
    Selector de opciones numeradas.
    
    Args:
        options: Lista de opciones a mostrar
        prompt: Mensaje a mostrar
        allow_cancel: Si permite cancelar con 0
        
    Returns:
        Índice seleccionado (0-indexed) o None si canceló
    """
    print()
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    if allow_cancel:
        print(f"  0. Cancelar")
    
    print()
    
    while True:
        try:
            user_input = input(f"  {prompt}: ").strip()
            
            if not user_input:
                continue
            
            choice = int(user_input)
            
            if choice == 0 and allow_cancel:
                return None
            
            if 1 <= choice <= len(options):
                return choice - 1
            
            print_error(f"Opción fuera de rango (1-{len(options)})")
            
        except ValueError:
            print_error("Por favor ingrese un número")


def input_list(
    prompt: str,
    default: Optional[List[str]] = None,
    validator: Optional[Callable[[str], bool]] = None,
    min_items: int = 0,
    max_items: int = 100,
) -> List[str]:
    """
    Input de lista de valores.
    
    Args:
        prompt: Mensaje a mostrar
        default: Lista por defecto
        validator: Función de validación por item
        min_items: Mínimo de items requeridos
        max_items: Máximo de items permitidos
        
    Returns:
        Lista de valores
    """
    if default is None:
        items = []
    else:
        items = list(default)
    
    print(f"\n  {prompt}")
    print(f"  (Deja vacío para terminar, 'list' para ver actual, 'clear' para vaciar)")
    print()
    
    while True:
        user_input = input(f"  Agregar item (ENTER para terminar): ").strip()
        
        if not user_input:
            break
        
        if user_input.lower() == "list":
            print(f"\n  Items actuales ({len(items)}):")
            for i, item in enumerate(items, 1):
                print(f"    {i}. {item}")
            print()
            continue
        
        if user_input.lower() == "clear":
            items = []
            print_success("Lista vaciada")
            continue
        
        if validator and not validator(user_input):
            print_error("Item inválido")
            continue
        
        if len(items) >= max_items:
            print_error(f"Máximo de {max_items} items")
            continue
        
        items.append(user_input)
        print_success(f"Item agregado: {user_input[:30]}...")
    
    if len(items) < min_items:
        print_error(f"Se requieren al menos {min_items} items")
        return []
    
    return items


def input_multi_select(
    options: List[Tuple[str, str]],
    prompt: str = "Seleccione opciones (números separados por coma)",
    min_select: int = 0,
    max_select: Optional[int] = None,
) -> List[str]:
    """
    Selección múltiple de opciones.
    
    Args:
        options: Lista de tuplas (valor, label)
        prompt: Mensaje a mostrar
        min_select: Mínimo a seleccionar
        max_select: Máximo a seleccionar (None = sin límite)
        
    Returns:
        Lista de valores seleccionados
    """
    if max_select is None:
        max_select = len(options)
    
    print()
    for i, (value, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    print()
    
    selected = []
    
    while True:
        user_input = input(f"  {prompt}: ").strip()
        
        if not user_input:
            if selected or min_select == 0:
                break
            print_error(f"Seleccione al menos {min_select} opción(es)")
            continue
        
        try:
            indices = [int(x.strip()) for x in user_input.split(",")]
            
            new_selections = []
            for idx in indices:
                if 1 <= idx <= len(options):
                    value = options[idx - 1][0]
                    if value not in selected:
                        new_selections.append(value)
                else:
                    print_warning(f"Opción {idx} fuera de rango")
            
            selected.extend(new_selections)
            
            if len(selected) >= min_select:
                break
            
        except ValueError:
            print_error("Formato inválido. Use números separados por coma")
    
    return selected


def input_float_range(
    prompt: str,
    default: Optional[float] = None,
    min_val: float = 0,
    max_val: float = 100,
) -> Optional[float]:
    """
    Input de float con validación de rango.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        
    Returns:
        Float validado o None
    """
    return input_number(
        prompt,
        default=default,
        num_type=float,
        min_val=min_val,
        max_val=max_val,
    )


def pause(message: str = "Presione ENTER para continuar...") -> None:
    """Pausa la ejecución esperando input del usuario."""
    input(f"\n  {_yellow(message)}")


# ============================================
# VALIDACIONES
# ============================================

def _validate_solana_address(address: str) -> bool:
    """
    Valida que una dirección sea un address válido de Solana.
    
    Args:
        address: String a validar
        
    Returns:
        True si es válido (base58, 32-44 caracteres)
    """
    if not address or len(address) < 32 or len(address) > 44:
        return False
    
    # Caracteres base58 válidos
    base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    
    return all(c in base58_chars for c in address)


def validate_float_positive(value: str) -> bool:
    """Valida que sea un float positivo."""
    try:
        return float(value.replace(",", ".")) > 0
    except ValueError:
        return False


def validate_int_positive(value: str) -> bool:
    """Valida que sea un int positivo."""
    try:
        return int(value) > 0
    except ValueError:
        return False


def validate_percentage(value: str) -> bool:
    """Valida que sea un porcentaje válido (0-100)."""
    try:
        v = float(value.replace(",", "."))
        return 0 <= v <= 100
    except ValueError:
        return False


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    print_header("WIDGETS TEST")
    
    # Test input_string
    name = input_string("Nombre", default="Test")
    print(f"  Resultado: {name}")
    
    # Test input_number
    age = input_number("Edad", default=25, num_type=int, min_val=1, max_val=150)
    print(f"  Resultado: {age}")
    
    # Test input_yes_no
    confirmed = input_yes_no("Confirmar", default=True)
    print(f"  Resultado: {confirmed}")
    
    # Test input_menu
    options = ["Opción A", "Opción B", "Opción C"]
    choice = input_menu(options)
    if choice is not None:
        print(f"  Seleccionado: {options[choice]}")
    
    # Test input_address
    address = input_address("Dirección del token")
    print(f"  Resultado: {address}")
    
    print_footer()
