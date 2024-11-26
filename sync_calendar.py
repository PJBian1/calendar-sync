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
        print(f"正在从 {self.toggle_url} 下载数据...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.toggle_url, headers=headers, timeout=30)
            response.raise_for_status()
            print(f"下载成功，响应状态码: {response.status_code}")
            print(f"响应内容长度: {len(response.text)} 字节")
            print("响应内容预览:")
            print(response.text[:200] if len(response.text) > 200 else response.text)
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"下载日历数据时发生错误: {str(e)}")
            print(f"完整错误信息: {repr(e)}")
            return None

    def process_calendar(self, ical_data):
        print("开始处理日历数据...")
        try:
            new_cal = Calendar()
            new_cal.add('prodid', '-//Toggle Plan Calendar Sync//CN')
            new_cal.add('version', '2.0')
            new_cal.add('x-wr-calname', 'Toggle Plan Events')

            print("解析原始日历数据...")
            original_cal = Calendar.from_ical(ical_data)

            event_count = 0
            filtered_count = 0
            for component in original_cal.walk():
                if component.name == "VEVENT":
                    dtstart = component.get('dtstart')
                    if dtstart and isinstance(dtstart.dt, datetime):
                        event = Event()
                        for key in component:
                            if key in ['summary', 'dtstart', 'dtend', 'description',
                                     'location', 'uid', 'created', 'last-modified']:
                                event.add(key, component[key])
                        new_cal.add_component(event)
                        event_count += 1
                    else:
                        filtered_count += 1

            print(f"处理完成. 总事件数: {event_count}, 已过滤事件数: {filtered_count}")
            return new_cal
        except Exception as e:
            print(f"处理日历数据时发生错误: {str(e)}")
            print(f"完整错误信息: {repr(e)}")
            return None

    def save_calendar(self, calendar):
        print(f"正在保存日历到: {self.output_path}")
        try:
            output_dir = Path(self.output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(self.output_path, 'wb') as f:
                calendar_data = calendar.to_ical()
                f.write(calendar_data)
            print(f"日历已成功保存，文件大小: {len(calendar_data)} 字节")
            return True
        except Exception as e:
            print(f"保存日历时发生错误: {str(e)}")
            print(f"完整错误信息: {repr(e)}")
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

    print(f"Toggle URL: {toggle_url[:20]}..." if toggle_url else "错误: 未设置TOGGLE_CALENDAR_URL")

    if not toggle_url:
        return False

    syncer = CalendarSync(toggle_url, output_path)
    return syncer.sync()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
