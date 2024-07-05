# Copyright (c) 2024 - Iván Moreno 
#  
# This software is licensed under the MIT License.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from utils.logger import logging

class ProjectSchedule:
    def __init__(self, workbook):
        self.workbook = workbook
        self.schedule_sheet = workbook['Schedule']
        self.available_resources_sheet = workbook['Available Resources']
        self.used_resources_sheet = workbook['Used Resources']
        self.dates_sheet = workbook.get('Dates', None)  # Podría no estar disponible

    def init(self, schedule_sheet, available_resources_sheet, used_resources_sheet, dates_sheet):
        # Inicializar las hojas de cálculo con las proporcionadas por Scheduler
        self.schedule_sheet = schedule_sheet
        self.available_resources_sheet = available_resources_sheet
        self.used_resources_sheet = used_resources_sheet
        self.dates_sheet = dates_sheet

    def update_schedule(self):
        # Aquí se implementaría la lógica para actualizar el horario
        # Por ahora, solo logueamos que se llamó a esta función
        logging.info("Updating schedule based on available resources")