import streamlit as st
import re
from datetime import datetime
import pyperclip
import locale # Import locale for month names if needed, though we'll use the extracted date format

# Optional: Set locale for Spanish month names if you were reformatting dates
# try:
#     locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') # For Linux/macOS
# except locale.Error:
#     try:
#         locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252') # For Windows
#     except locale.Error:
#         st.warning("Could not set locale for Spanish month names. Dates might use English names if reformatted.")

def parse_voucher(text):
    # Updated patterns to match the provided voucher format
    patterns = {
        # Allow variable spaces around the colon
        'date': r'Fecha\s*:\s*(\d{2}/\d{2}/\d{4})',
        # Capture account number (alphanumeric starting CR) and name (assuming CAPS_WITH_UNDERSCORES)
        'account_and_name': r'Cuenta origen([A-Z0-9]+)\s+([A-Z_]+)',
        # Match 'Referencia' followed immediately by digits
        'reference': r'Referencia(\d+)',
        # Match 'Descripción' followed immediately by the concept text
        'concept': r'Descripción([^\n]+)',
        # Match 'Monto', capture the amount (digits, commas, optional dot), and the 3-letter currency code
        'amount_and_currency': r'Monto\s*([\d,]+\.?\d*)\s+([A-Z]{3})',
    }

    data = {}
    # Extract account and name first as they are on the same line
    match_acc_name = re.search(patterns['account_and_name'], text)
    if match_acc_name:
        data['account'] = match_acc_name.group(1).strip()
        # Clean up name: replace underscores, title case
        raw_name = match_acc_name.group(2).strip()
        data['name'] = raw_name.replace('_', ' ').title() # Convert to title case (e.g., Giovanni Mora Castil)

    # Extract amount and currency
    match_amount_curr = re.search(patterns['amount_and_currency'], text)
    if match_amount_curr:
        data['amount'] = match_amount_curr.group(1).strip().replace(',', '') # Remove commas for potential float conversion later
        data['currency'] = match_amount_curr.group(2).strip()

    # Extract remaining single fields
    for key in ['date', 'reference', 'concept']:
        match = re.search(patterns[key], text)
        if match:
            data[key] = match.group(1).strip()

    # Clean up the concept field (remove underscores and trailing underscore if present)
    if 'concept' in data:
        data['concept'] = data['concept'].replace('_', ' ').strip()
        # Try to extract Filial number from the concept
        filial_match = re.search(r'Filial\s+(\d+)', data['concept'], re.IGNORECASE)
        if filial_match:
            data['filial'] = filial_match.group(1)

    # If name wasn't found via 'Cuenta origen', provide a default (optional)
    if 'name' not in data:
        data['name'] = 'Giovanni Mora Castillo' # Fallback if regex fails

    # If filial wasn't found, provide a default
    if 'filial' not in data:
        data['filial'] = '25' # Fallback if regex fails

    return data

def generate_notification(data):
    # Use the extracted date directly, format fallback if needed
    extracted_date = data.get('date', datetime.now().strftime("%d/%m/%Y"))

    # Use extracted name and filial, with fallbacks defined in parse_voucher
    owner_name = data.get('name', 'Propietario Desconocido')
    filial_num = data.get('filial', 'N/A')

    # Combine amount and currency
    amount_str = f"{data.get('amount', 'N/A')} {data.get('currency', '')}".strip()

    notification = f"""# Notificación de Pago de Mantenimiento

**Para:** Administración del Condominio Estancias de San Joaquin

**De:** {owner_name}, Propietario de Filial #{filial_num}

**Fecha:** {extracted_date}

Por medio de la presente, se notifica que se ha realizado el pago por concepto de mantenimiento del condominio, según los siguientes detalles:

## Información del Pago

- **Método de Pago:** SINPE MÓVIL
- **Propietario:** {owner_name}
- **Filial:** #{filial_num}
- **Monto:** {amount_str}
- **Fecha y Hora de la Transacción:** {extracted_date} (Nota: Hora no disponible en el comprobante)
- **Número de Referencia:** {data.get('reference', 'N/A')}
- **Concepto:** {data.get('concept', 'N/A')}

## Detalles de la Transacción

- **Cuenta Origen:** {data.get('account', 'N/A')}
- **Banco:** BAC Credomatic (Asumido)

Se solicita amablemente confirmar la recepción de este pago y aplicarlo a la cuenta correspondiente de la Filial #{filial_num}.

Para cualquier consulta adicional o aclaración, favor comunicarse con el propietario.

Atentamente,

{owner_name}
Propietario Filial #{filial_num}
Condominio Estancias de San Joaquin"""

    return notification

def main():
    st.title("Generador de Notificación de Pago de Condominio")

    voucher_text = st.text_area("Pegue el texto del comprobante bancario aquí:", height=200)

    if st.button("Generar Notificación"):
        if voucher_text:
            data = parse_voucher(voucher_text)

            # Optional: Display extracted data for debugging
            # st.write("Extracted Data:")
            # st.json(data)

            notification = generate_notification(data)

            st.markdown("## Notificación Generada")
            st.markdown(notification)

            # Use a unique key for the copy button to avoid conflicts if reused
            if st.button("Copiar Notificación", key="copy_button"):
                try:
                    pyperclip.copy(notification)
                    st.success("Notificación copiada al portapapeles!")
                except Exception as e:
                    st.error(f"No se pudo copiar al portapapeles: {e}")
                    st.info("Es posible que necesite instalar 'xclip' o 'xsel' en Linux, o que pyperclip no funcione en entornos restringidos como Streamlit Cloud sin configuración adicional.")

        else:
            st.warning("Por favor, ingrese el texto del comprobante bancario.")

if __name__ == "__main__":
    main()
