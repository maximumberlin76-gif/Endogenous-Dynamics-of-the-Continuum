import numpy as np
import matplotlib.pyplot as plt


class MarnovOrganicMatrixGenerator:
    def __init__(self, grid_size=64, dx=0.05):
        self.grid_size = grid_size
        self.dx = dx
        self.shape = (grid_size, grid_size, grid_size)

        # Инициализируем матрицу плотности органического вещества (био-матрица)
        self.bio_density = np.zeros(self.shape)

        # Начальная точка инициации ("клетка-предок" или волновой фокус в центре)
        self.bio_density[
            grid_size // 2,
            grid_size // 2,
            grid_size // 2
        ] = 1.0

    def generate_asymmetric_c3_field(self, epsilon=0.236068):
        """
        Генерация 6D кубического замка C^3 с золотым сечением (иррациональностью).

        epsilon = 0.236068
        производная от Золотого Сечения, обеспечивающая живую асимметрию.
        """
        x, y, z = np.indices(self.shape)

        cx = self.grid_size // 2
        cy = self.grid_size // 2
        cz = self.grid_size // 2

        # Строим базовый тор
        r_tor = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        d_tor = np.sqrt((r_tor - self.grid_size // 5) ** 2 + (z - cz) ** 2)

        # Вводим иррациональную угловую асимметрию
        theta = np.arctan2(y - cy, x - cx)
        asymmetry_factor = 1.0 + epsilon * np.sin(3.0 * theta + z * 0.1)

        # Результирующий кубический замок удержания объема
        C3 = asymmetry_factor * np.exp(-(d_tor ** 2) / (2.0 * 3.0 ** 2))

        return C3

    def grow_organic_matrix(self, C3, steps=10):
        """
        Рекурсивный потактовый рост био-структуры.

        Каждый шаг учитывает нелинейную диффузию и иррациональное давление C^3.
        """
        dt = 0.1
        D_coef = 0.15  # Коэффициент диффузии континуума

        for step in range(steps):
            # Вычисляем пространственный Лапласиан био-плотности центральными разностями
            laplacian = np.zeros_like(self.bio_density)

            # Стандартный сдвиг для расчета диффузии в 3D
            for axis in range(3):
                laplacian += (
                    np.roll(self.bio_density, 1, axis=axis)
                    + np.roll(self.bio_density, -1, axis=axis)
                    - 2.0 * self.bio_density
                ) / (self.dx ** 2)

            # Уравнение EDS живой матрицы:
            # Growth = Диффузия + Удержание(C^3) - Иррациональное насыщение
            # Нелинейный член (bio_density^2) ограничивает избыточный рост,
            # формируя мембраны / границы
            growth_rate = D_coef * laplacian + 2.0 * C3 * (1.0 - self.bio_density)

            self.bio_density += dt * growth_rate

            # Симулируем рекурсивный фрактальный почкующийся сдвиг
            # На каждом шаге асимметрия C^3 "проедает" в био-массе фрактальные каналы
            self.bio_density = np.clip(self.bio_density, 0.0, 1.0)

    def visualize_organic_slice(self):
        """
        Визуализация структуры полученной живой матрицы в разрезе.
        """
        mid_z = self.grid_size // 2
        mid_y = self.grid_size // 2

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        fig.suptitle(
            "Протокол Марнова — Манифестация Органической Матрицы (3D)",
            fontsize=13,
            fontweight="bold"
        )

        # Горизонтальный срез XY
        im1 = ax1.imshow(
            self.bio_density[:, :, mid_z],
            cmap="YlGnBu",
            origin="lower"
        )
        ax1.set_title("Срез био-матрицы XY (Стволовое сечение)")
        ax1.set_xlabel("Проекция X")
        ax1.set_ylabel("Проекция Y")
        fig.colorbar(im1, ax=ax1, label="Плотность органической ткани")

        # Вертикальный срез XZ
        im2 = ax2.imshow(
            self.bio_density[mid_y, :, :],
            cmap="YlGnBu",
            origin="lower"
        )
        ax2.set_title("Срез био-матрицы XZ (Капиллярное ветвление)")
        ax2.set_xlabel("Проекция Z")
        ax2.set_ylabel("Проекция X")
        fig.colorbar(im2, ax=ax2, label="Плотность органической ткани")

        plt.tight_layout()
        plt.show()


# ==============================================================================
# ЗАПУСК ГЕНЕРАЦИИ ЖИВОЙ СТРУКТУРЫ
# ==============================================================================

if __name__ == "__main__":
    generator = MarnovOrganicMatrixGenerator(grid_size=64)

    print("1. Активация 6D фазового замка с иррациональностью Золотого Сечения...")
    C3_field = generator.generate_asymmetric_c3_field()

    print("2. Запуск рекурсивного каскада роста органической матрицы (15 тактов)...")
    generator.grow_organic_matrix(C3_field, steps=15)

    print("3. Вывод фрактального среза проявления живой системы:")
    generator.visualize_organic_slice()
