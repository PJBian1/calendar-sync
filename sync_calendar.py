import requests
from datetime import datetime
import pytz
from icalendar import Calendar, Event
import os
from pathlib import Path

class CalendarSync:
    def __init__(self, toggle_url, output_path):
        self.toggle_url = toggle_url
        self.output_path = output_path
        self.local_timezone = pytz.timezone('Asia/Shanghai')

    def download_calendar(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.toggle_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"下载日历数据时发生错误: {str(e)}")
            return None

    def process_calendar(self, ical_data):
        try:
            new_cal = Calendar()
            new_cal.add('prodid', '-//Toggle Plan Calendar Sync//CN')
            new_cal.add('version', '2.0')
            new_cal.add('x-wr-calname', 'Toggle Plan Events')
            
            original_cal = Calendar.from_ical(ical_data)
            
            for component in original_cal.walk():
                if component.name == "VEVENT":
                    dtstart = component.get('dtstart')
                    if dtstart and isinstance(dtstart.dt, datetime):  # 只处理具体时间的事件
                        event = Event()
                        for key in component:
                            if key in ['summary', 'dtstart', 'dtend', 'description', 
                                     'location', 'uid', 'created', 'last-modified']:
                                event.add(key, component[key])
                        new_cal.add_component(event)
            
            return new_cal
        except Exception as e:
            print(f"处理日历数据时发生错误: {str(e)}")
            return None

    def save_calendar(self, calendar):
        try:
            output_dir = Path(self.output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_path, 'wb') as f:
                f.write(calendar.to_ical())
            print(f"日历已更新: {self.output_path}")
            return True
        except Exception as e:
            print(f"保存日历时发生错误: {str(e)}")
            return False

    def sync(self):
        print(f"开始同步 - {datetime.now()}")
        ical_data = self.download_calendar()
        if not ical_data:
            return False
            
        new_calendar = self.process_calendar(ical_data)
        if not new_calendar:
            return False
            
        return self.save_calendar(new_calendar)

def main():
    toggle_url = os.getenv('TOGGLE_CALENDAR_URL')
    output_path = os.getenv('CALENDAR_OUTPUT_PATH', 'calendar.ics')
    
    if not toggle_url:
        print("错误: 未设置TOGGLE_CALENDAR_URL环境变量")
        return False
    
    syncer = CalendarSync(toggle_url, output_path)
    return syncer.sync()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
