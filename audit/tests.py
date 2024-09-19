from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import Audit, Data


class AuditUploadTest(TestCase):
    def test_csv_file_upload_and_processing(self):
        # Создаём тестовый CSV-файл
        csv_content = b"price,count,add_cost,company,product\n100,10,1,First,f_prod\n200,20,2,Second,s_prod"
        uploaded_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        # Загружаем файл через POST-запрос
        response = self.client.post('/data/', {'file': uploaded_file})

        # Проверяем, что запрос был успешен
        self.assertEqual(response.status_code, 302)  # Редирект после успешной загрузки

        # Проверяем, что данные были сохранены в Data
        self.assertEqual(Data.objects.count(), 2)

        # Проверяем имя и email первого объекта
        first_record = Data.objects.first()
        self.assertEqual(first_record.company, 'First')
        self.assertEqual(first_record.product, 'f_prod')

        # Проверяем, что дата загрузки данных (upload_date) была установлена правильно
        current_time = timezone.now()
        self.assertAlmostEqual(first_record.upload_date, current_time, delta=timezone.timedelta(seconds=10))

        # Проверяем, что файл был удалён после обработки
        self.assertEqual(Audit.objects.count(), 0)
