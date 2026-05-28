# Script para agregar debug prints en la ruta planes_list
with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar debug prints
old_route = '''@admin_bp.route('/planes')
@admin_required
def planes_list():
    """Listado de planes"""
    planes = AdminService.get_planes_list()
    return render_template('admin/planes.html', plans=planes)'''

new_route = '''@admin_bp.route('/planes')
@admin_required
def planes_list():
    """Listado de planes"""
    planes = AdminService.get_planes_list()
    print(f"DEBUG ROUTE: planes = {planes}")
    print(f"DEBUG ROUTE: len(planes) = {len(planes) if plans else 0}")
    return render_template('admin/planes.html', plans=plans)'''

content = content.replace(old_route, new_route)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Debug prints agregados en planes_list")
