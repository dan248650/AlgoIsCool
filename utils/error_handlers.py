from flask import jsonify, request, render_template


def register_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404

        return render_template('errors/error.html',
                               error='Endpoint not found'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500

        return render_template('errors/error.html',
                               error=f'Internal server error: {error}'), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500

        return render_template('errors/error.html',
                               error=f'Unhandled exception: {error}'), 500
