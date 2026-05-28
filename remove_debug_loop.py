# Script para eliminar el debug loop
with open('app/templates/admin/empresas_crear.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_next = 0
for i, line in enumerate(lines):
    # Detectar inicio del debug loop
    if '<!-- Debug loop -->' in line:
        skip_next = 4  # Saltar 4 líneas (el comentario y el bucle for)
        continue
    
    if skip_next > 0:
        skip_next -= 1
        continue
    
    new_lines.append(line)

with open('app/templates/admin/empresas_crear.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Debug loop eliminado")
