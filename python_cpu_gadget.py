import gi
import math
import cairo
import psutil
import threading
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk  # Gdk ekledik

class CircleBands(Gtk.DrawingArea):
    # (CircleBands sınıfının içeriği burada, değişiklik yok)
    def __init__(self):
        super().__init__()
        self.cpu_usage = 0  # Başlangıç CPU kullanımı
        self.connect("draw", self.on_draw)
        self.start_cpu_monitoring()  # CPU izlemeyi başlat

    def start_cpu_monitoring(self):
        """CPU kullanımını düzenli olarak günceller."""
        def update_cpu_usage():
            self.cpu_usage = psutil.cpu_percent()
            # Çizimi yeniden tetikle (GUI thread'inde yapılması gerekiyor)
            GLib.idle_add(self.queue_draw)
            return True  # Her saniye tekrarla

        # Her saniyede bir CPU kullanımını güncelle
        GLib.timeout_add_seconds(1, update_cpu_usage)

    def on_draw(self, widget, cr):
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        center_x, center_y = width / 2, height / 2
        outer_radius = min(width, height) / 2 - 10
        band_width = 10
        inner_band_width = 8  # İç bandın genişliği

        self.draw_band(cr, center_x, center_y, outer_radius, band_width, clockwise=True, offset=0)
        self.draw_band(cr, center_x, center_y, outer_radius - band_width, band_width, clockwise=False, offset=180)
        inner_radius = outer_radius - 2 * band_width
        self.draw_inner_gradient_band(cr, center_x, center_y, inner_radius, inner_band_width)
        self.draw_numbers(cr, center_x, center_y, inner_radius - inner_band_width / 2)  # Sayıları çiz
        self.draw_needle(cr, center_x, center_y, inner_radius / 2, self.cpu_usage) # İğneyi çiz

    def draw_band(self, cr, cx, cy, radius, band_width, clockwise=True, offset=0):
        step = 1.2  # Açısal hassasiyeti artırarak boşlukları kapatma
        for angle in range(0, 360, int(step)):
            adjusted_angle = (angle + offset) % 360
            theta1 = math.radians(angle)
            theta2 = math.radians(angle + step)

            # Gradyen hızını değiştirme: Siyah -> Açık Gri geçişi hızlı, Açık Gri geçişi hızlı, Açık Gri uzun sürsün
            gradient = 0.5 + 0.5 * math.sin(math.radians(adjusted_angle) * 1.5)  # 1.5 ile hızlandırma
            cr.set_source_rgb(gradient, gradient, gradient)

            x1, y1 = cx + radius * math.cos(theta1), cy + radius * math.sin(theta1)
            x2, y2 = cx + (radius + band_width) * math.cos(theta1), cy + (radius + band_width) * math.sin(theta1)
            x3, y3 = cx + (radius + band_width) * math.cos(theta2), cy + (radius + band_width) * math.sin(theta2)
            x4, y4 = cx + radius * math.cos(theta2), cy + radius * math.sin(theta2)

            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.line_to(x3, y3)
            cr.line_to(x4, y4)
            cr.close_path()
            cr.fill()

    def draw_inner_gradient_band(self, cr, cx, cy, radius, band_width):
        rotation_offset = 210
        start_angle = (180 + rotation_offset) % 480  # Adjusted start angle (degrees)
        end_angle = (-60 + rotation_offset) % 480  # Adjusted end angle (degrees), goes past 0 to 330
        step = 1.2

        total_range = start_angle - end_angle if start_angle > end_angle else start_angle + (360-end_angle)

        for i, angle in enumerate(range(end_angle, start_angle, int(step))):
            adjusted_angle = angle % 360  # Ensure angle remains within 0-360

            theta1 = math.radians(adjusted_angle)
            theta2 = math.radians(adjusted_angle + step)

            # Normalise to 0-1
            t = (i * step) / total_range if total_range > 0 else 0

            # Define colour transitions
            if t < 0.33:
                # Green to Yellow
                r = t * 3  # Scale t to go from 0 to 1
                g = 1
                b = 0
            elif t < 0.66:
                # Yellow to Red
                r = 1
                g = 1 - (t - 0.33) * 3 # Scale (t-0.33) to go from 1 to 0
                b = 0
            else:
                # Red remains
                r = 1
                g = 0
                b = 0

            cr.set_source_rgb(r, g, b)

            x1, y1 = cx + radius * math.cos(theta1), cy + radius * math.sin(theta1)
            x2, y2 = cx + (radius + band_width) * math.cos(theta1), cy + (radius + band_width) * math.sin(theta1)
            x3, y3 = cx + (radius + band_width) * math.cos(theta2), cy + (radius + band_width) * math.sin(theta2)
            x4, y4 = cx + radius * math.cos(theta2), cy + radius * math.sin(theta2)

            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.line_to(x3, y3)
            cr.line_to(x4, y4)
            cr.close_path()
            cr.fill()

    def draw_numbers(self, cr, cx, cy, radius):
        start_angle = 135  # Saat 8 yönü
        end_angle = 45    # Saat 4 yönü
        num_steps = 11    # 0'dan 100'e kadar 11 sayı (10'ar artışla)
        angle_range = (end_angle - start_angle) % 360
        if angle_range < 0:
            angle_range += 360
        angle_step = angle_range / (num_steps - 1)

        cr.set_source_rgb(1, 1, 1)  # Metin rengi: Beyaz
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12) # Yazı tipi boyutu

        for i in range(num_steps):
            angle = (start_angle + i * angle_step) % 360
            x = cx + radius * math.cos(math.radians(angle))
            y = cy + radius * math.sin(math.radians(angle))
            text = str(i * 10)

            # Metin boyutunu al
            (x_bearing, y_bearing, width, height, x_advance, y_advance) = cr.text_extents(text)

            # Metni ortala
            x -= width / 2
            y += height / 2

            cr.move_to(x, y)
            cr.show_text(text)

    def draw_needle(self, cr, cx, cy, length, cpu_usage):
        """CPU kullanımını gösteren iğneyi çizer."""
        # CPU kullanımını 0-1 aralığına normalleştir
        normalized_usage = cpu_usage / 30.0

        # İğnenin açısını hesapla (45 derece ile 135 derece arasında)
        angle = 130 + normalized_usage * 90  # Toplam aralık 90 derece

        # İğnenin bitiş noktasının koordinatlarını hesapla
        # Uzunluğu %40 artır
        extended_length = length * 1.4
        x = cx + extended_length * math.cos(math.radians(angle))
        y = cy + extended_length * math.sin(math.radians(angle))

        # İğneyi çiz
        # Çizgi kalınlığını artır
        cr.set_line_width(0.2)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.8) 
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(cx, cy)
        cr.line_to(x, y)
        cr.stroke_preserve()
        cr.set_source_rgba(1.0, 0.0, 0.0, 1.0)  # İğne rengi: Kırmızı
        cr.set_line_width(6)
        cr.stroke()

class GradientCirclesApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="CPU Usage Meter")  # Pencere başlığı
        self.set_default_size(200, 200)
        self.set_skip_taskbar_hint (True)
        self.set_keep_below(True)
        self.set_decorated(False)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.set_app_paintable(True)

        # Sürükleme için gerekli değişkenler
        self.drag_active = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        self.connect("destroy", Gtk.main_quit)
        self.connect("button-press-event", self.on_button_press)  # Mouse'a basma
        self.connect("button-release-event", self.on_button_release) # Mouse'u bırakma
        self.connect("motion-notify-event", self.on_motion_notify)   # Mouse hareketleri

        # Pencereye mouse hareketlerini algılaması için izin ver
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK |   # Gtk.EventMask -> Gdk.EventMask
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        self.drawing_area = CircleBands()  # Çizim alanını oluştur
        self.add(self.drawing_area)          # Çizim alanını pencereye ekle
        self.show_all()

    def on_button_press(self, widget, event):
        """Mouse düğmesine basıldığında çağrılır."""
        if event.button == 1:  # Sol mouse tuşu
            self.drag_active = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            return True  # Event'i işle

        return False

    def on_button_release(self, widget, event):
        """Mouse düğmesi bırakıldığında çağrılır."""
        self.drag_active = False
        return True

    def on_motion_notify(self, widget, event):
        """Mouse hareket ettiğinde çağrılır."""
        if self.drag_active:
            # Pencerenin mevcut konumunu al
            x, y = self.get_position()

            # Yeni konumu hesapla
            new_x = x + (event.x - self.drag_start_x)
            new_y = y + (event.y - self.drag_start_y)

            # Pencereyi yeni konuma taşı
            self.move(new_x, new_y)
            return True

        return False

if __name__ == "__main__":
    app = GradientCirclesApp()
    Gtk.main()
