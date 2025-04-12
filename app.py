from flask import Flask, render_template, request, send_file, redirect
from PIL import Image, ImageFilter, ImageEnhance
import os
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def apply_sepia(img):
    img = img.convert("RGB")
    width, height = img.size
    pixels = img.load()

    for py in range(height):
        for px in range(width):
            r, g, b = pixels[px, py]

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))

    return img


def apply_vignette(img, percent=30):
    img = img.convert("RGB")
    width, height = img.size
    pixels = img.load()

    center_x, center_y = width // 2, height // 2
    max_dist = ((center_x ** 2 + center_y ** 2) ** 0.5)
    vignette_strength = percent / 100

    for y in range(height):
        for x in range(width):
            dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            factor = 1 - (dist / max_dist) * vignette_strength

            r, g, b = pixels[x, y]
            pixels[x, y] = (int(r * factor), int(g * factor), int(b * factor))

    return img


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/basic', methods=['GET', 'POST'])
def basic_style():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '' or not allowed_file(file.filename):
            return redirect(request.url)

        img = Image.open(file.stream).convert('RGB')  # always convert for consistency

        style = request.form.get('style', 'original')
        intensity = float(request.form.get('intensity', '1.0'))

        if style == 'black_white':
            styled_img = img.convert('L')
        elif style == 'sepia':
            styled_img = apply_sepia(img)
        elif style == 'sketch':
            styled_img = img.convert('L').filter(ImageFilter.CONTOUR)
        elif style == 'blur':
            styled_img = img.filter(ImageFilter.GaussianBlur(radius=5 * intensity))
        elif style == 'enhance':
            enhancer = ImageEnhance.Color(img)
            styled_img = enhancer.enhance(intensity)
        elif style == 'vignette':
            styled_img = apply_vignette(img, percent=int(30 * intensity))
        else:
            styled_img = img

        img_io = io.BytesIO()
        if styled_img.mode == 'L':
            styled_img.save(img_io, 'PNG')
            mimetype = 'image/png'
        else:
            styled_img.save(img_io, 'JPEG', quality=90)
            mimetype = 'image/jpeg'

        img_io.seek(0)
        return send_file(img_io, mimetype=mimetype)

    return render_template('basic.html')


if __name__ == '__main__':
    app.run(debug=True)
