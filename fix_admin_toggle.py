# Script más robusto para arreglar admin.py
with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Primero, eliminar la línea duplicada
lines = content.split('\n')
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    if 'return render_template' in line and i == 159:
        skip_next = True
        continue
    new_lines.append(line)

content = '\n'.join(new_lines)

# Ahora buscar y reemplazar la sección de planes_list para agregar planes_toggle
old_section = '''@admin_bp.route('/planes')
@admin_required
def planes_list():
    """Listado de planes"""
    plans = AdminService.get_planes_list()
    return render_template('admin/planes.html', plans=planes)

@admin_bp.route('/planes/crear', methods=['GET', 'POST'])'''

new_section = '''@admin_bp.route('/planes')
@admin_required
def planes_list():
    """Listado de planes"""
    plans = AdminService.get_planes_list()
    return render_template('admin/planes.html', plans=planes)

@admin_bp.route('/planes/<int:plan_id>/toggle', methods=['POST'])
@admin_required
def planes_toggle(plan_id):
    """Activar/Desactivar plan"""
    try:
        plan = AdminService.toggle_plan_status(plan_id)
        if plan:
            estado = 'activado' if plan.activo else 'desactivado'
            flash(f'Plan {plan.nombre} {estado} exitosamente', 'success')
        else:
            flash('Plan no encontrado', 'error')
    except Exception as e:
        flash(f'Error al cambiar estado del plan: {str(e)}', 'error')
    
    return redirect(url_for('admin.planes_list'))

@admin_bp.route('/planes/crear', methods=['GET', 'POST'])'''

if old_section in content:
    content = content.replace(old_section, new_section)
    print("Ruta planes_toggle agregada correctamente")
else:
    print("No se encontró la sección a reemplazar")

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo admin.py actualizado")
