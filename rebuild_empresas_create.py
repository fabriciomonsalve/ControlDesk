# Script para reconstruir completamente la función empresas_create
with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la función completa empresas_create
old_function = '''@admin_bp.route('/empresas/crear', methods=['GET', 'POST'])
@admin_required
def empresas_create():
    """Crear nueva empresa"""
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'rut_empresa': request.form.get('rut_empresa'),
            'correo': request.form.get('correo'),
            'telefono': request.form.get('telefono'),
            'direccion': request.form.get('direccion'),
            'estado': request.form.get('estado', 'activa'),
            'pin': request.form.get('pin'),
            'plan_id': int(request.form.get('plan_id')) if request.form.get('plan_id') else None,
            'fecha_inicio_plan': request.form.get('fecha_inicio_plan'),
            'fecha_expiracion_plan': request.form.get('fecha_expiracion_plan')
        }
        
        try:
            empresa = AdminService.create_empresa(data)
            flash(f'Empresa {empresa.nombre} creada exitosamente', 'success')
            return redirect(url_for('admin.empresas_list'))
        except Exception as e:
            flash(f'Error al crear empresa: {str(e)}', 'error')
    
    try:
        plans = AdminService.get_planes_list()
    except Exception as e:
        print(f"ERROR getting planes: {e}")
        plans = []
    
    return render_template('admin/empresas_crear.html', plans=plans)'''

new_function = '''@admin_bp.route('/empresas/crear', methods=['GET', 'POST'])
@admin_required
def empresas_create():
    """Crear nueva empresa"""
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'rut_empresa': request.form.get('rut_empresa'),
            'correo': request.form.get('correo'),
            'telefono': request.form.get('telefono'),
            'direccion': request.form.get('direccion'),
            'estado': request.form.get('estado', 'activa'),
            'pin': request.form.get('pin'),
            'plan_id': int(request.form.get('plan_id')) if request.form.get('plan_id') else None,
            'fecha_inicio_plan': request.form.get('fecha_inicio_plan'),
            'fecha_expiracion_plan': request.form.get('fecha_expiracion_plan')
        }
        
        try:
            empresa = AdminService.create_empresa(data)
            flash(f'Empresa {empresa.nombre} creada exitosamente', 'success')
            return redirect(url_for('admin.empresas_list'))
        except Exception as e:
            flash(f'Error al crear empresa: {str(e)}', 'error')
    
    plans = AdminService.get_planes_list()
    return render_template('admin/empresas_crear.html', plans=plans)'''

if old_function in content:
    content = content.replace(old_function, new_function)
    print("Función empresas_create reconstruida correctamente")
else:
    print("No se encontró la función empresas_create original")

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo admin.py actualizado")
