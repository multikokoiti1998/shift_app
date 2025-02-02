from django.shortcuts import render, redirect
from django.http import JsonResponse
import pandas as pd
import os
import calendar
from datetime import datetime, timedelta

# 技師データを保存するファイル
TECHS_FILE = 'static/techs.csv'
AB_TEAMS_FILE = 'static/ab_teams.csv'

# 技師リストの初期化
all_techs = []
catheter_team = []
non_catheter_team = []
a_team = []
b_team = []
duty_count = {}
last_duty = {}

# 制約条件
MAX_DUTY_CATHETER = 4
MAX_DUTY_NON_CATHETER = 3

def load_techs():
    global all_techs, catheter_team, non_catheter_team, a_team, b_team, duty_count, last_duty
    if os.path.exists(TECHS_FILE):
        df = pd.read_csv(TECHS_FILE, encoding='utf-8-sig')
        all_techs = df['技師名'].tolist()
        catheter_team = df[df['カテーテル可'] == 1]['技師名'].tolist()
        non_catheter_team = df[df['カテーテル可'] == 0]['技師名'].tolist()
    else:
        df = pd.DataFrame({'技師名': all_techs, 'カテーテル可': [0] * len(all_techs)})
        df.to_csv(TECHS_FILE, index=False, encoding='utf-8-sig')
    
    if os.path.exists(AB_TEAMS_FILE):
        df = pd.read_csv(AB_TEAMS_FILE, encoding='utf-8-sig')
        a_team = df[df['班'] == 'A']['技師名'].tolist()
        b_team = df[df['班'] == 'B']['技師名'].tolist()
    
    duty_count = {name: 0 for name in all_techs}
    last_duty = {name: None for name in all_techs}

def index(request):
    """技師リストとシフトデータを表示するビュー"""
    load_techs()
    
    shift_file = os.path.join('static', 'shift_schedule.csv')
    shift_data = []
    if os.path.exists(shift_file):
        df = pd.read_csv(shift_file, encoding='utf-8-sig')
        shift_data = df.to_dict(orient='records')
    
    return render(request, 'index.html', {
        'all_techs': all_techs,
        'catheter_team': catheter_team,
        'non_catheter_team': non_catheter_team,
        'a_team': a_team,
        'b_team': b_team,
        'shift_data': shift_data
    })

def assign_teams(request):
    """A/B班とカテーテル可否を登録"""
    global a_team, b_team, catheter_team, non_catheter_team
    if request.method == "POST":
        catheter_team = request.POST.getlist("catheter_team")
        non_catheter_team = [tech for tech in all_techs if tech not in catheter_team]
        a_team = request.POST.getlist("a_team")
        b_team = request.POST.getlist("b_team")
        df_teams = pd.DataFrame({"技師名": a_team + b_team, "班": ["A"] * len(a_team) + ["B"] * len(b_team)})
        df_teams.to_csv(AB_TEAMS_FILE, index=False, encoding="utf-8-sig")
    return redirect("index")

def delete_tech(request, tech_name):
    """技師を削除"""
    global all_techs, catheter_team, non_catheter_team
    if tech_name in all_techs:
        all_techs.remove(tech_name)
        if tech_name in catheter_team:
            catheter_team.remove(tech_name)
        if tech_name in non_catheter_team:
            non_catheter_team.remove(tech_name)
        df_techs = pd.DataFrame({'技師名': all_techs, 'カテーテル可': [1 if tech in catheter_team else 0 for tech in all_techs]})
        df_techs.to_csv(TECHS_FILE, index=False, encoding='utf-8-sig')
    return redirect('index')
def add_tech(request):
    """新しい技師を登録するビュー"""
    global all_techs, catheter_team, non_catheter_team

    if request.method == "POST":
        new_tech = request.POST.get("new_tech")
        catheter_ability = int(request.POST.get("catheter_ability", 0))  # カテーテル可否

        if new_tech and new_tech not in all_techs:
            all_techs.append(new_tech)
            if catheter_ability:
                catheter_team.append(new_tech)
            else:
                non_catheter_team.append(new_tech)

            # CSV に保存
            df_techs = pd.DataFrame({
                "技師名": all_techs, 
                "カテーテル可": [1 if tech in catheter_team else 0 for tech in all_techs]
            })
            df_techs.to_csv(TECHS_FILE, index=False, encoding="utf-8-sig")

    return redirect("index")
def assign_ab_team(request):
    """A/B班のメンバーを登録"""
    global a_team, b_team

    if request.method == "POST":
        a_team = request.POST.getlist("a_team")
        b_team = request.POST.getlist("b_team")

        # CSVに保存
        df_teams = pd.DataFrame({
            "技師名": a_team + b_team,
            "班": ["A"] * len(a_team) + ["B"] * len(b_team)
        })
        df_teams.to_csv(AB_TEAMS_FILE, index=False, encoding="utf-8-sig")

    return redirect("index")

from django.shortcuts import render, redirect
import pandas as pd
import os
import calendar
from datetime import datetime, timedelta

TECHS_FILE = 'static/techs.csv'
AB_TEAMS_FILE = 'static/ab_teams.csv'
HOLIDAYS_FILE = 'static/holidays.csv'
SHIFT_FILE = 'static/shift_schedule.csv'

MAX_DUTY_CATHETER = 4
MAX_DUTY_NON_CATHETER = 3

def load_techs():
    """技師データをロード"""
    global all_techs, catheter_team, non_catheter_team, a_team, b_team, duty_count, last_duty
    all_techs, catheter_team, non_catheter_team, a_team, b_team = [], [], [], [], []
    duty_count = {}
    last_duty = {}

    if os.path.exists(TECHS_FILE):
        df = pd.read_csv(TECHS_FILE, encoding='utf-8-sig')
        all_techs = df['技師名'].tolist()
        catheter_team = df[df['カテーテル可'] == 1]['技師名'].tolist()
        non_catheter_team = df[df['カテーテル可'] == 0]['技師名'].tolist()

    if os.path.exists(AB_TEAMS_FILE):
        df = pd.read_csv(AB_TEAMS_FILE, encoding='utf-8-sig')
        a_team = df[df['班'] == 'A']['技師名'].tolist()
        b_team = df[df['班'] == 'B']['技師名'].tolist()

    duty_count = {name: 0 for name in all_techs}
    last_duty = {name: None for name in all_techs}

def load_holidays(year, month):
    """指定された年月の祝日リストを取得"""
    holidays = set()
    if os.path.exists(HOLIDAYS_FILE):
        df = pd.read_csv(HOLIDAYS_FILE, encoding='utf-8-sig')
        df['日付'] = pd.to_datetime(df['日付'], format='%Y-%m-%d')
        holidays = set(df[df['日付'].dt.year == year][df['日付'].dt.month == month]['日付'])
    return holidays
    #土曜日、出勤班を特定
def get_team_for_saturday(base_saturday, target_date):
    """
    base_saturday: 最初のB班の出勤日 (例: 2025-01-04)
    target_date: 判定したい土曜日の日付 (例: 2025-02-01)
    """
    base_saturday = datetime.strptime(base_saturday, "%Y-%m-%d")
    target_date = datetime.strptime(target_date, "%Y-%m-%d")
    
    weeks_difference = (target_date - base_saturday).days // 7
    return "B班" if weeks_difference % 2 == 0 else "A班"
def create_shift_schedule(request):
    """シフトを作成し、制約を満たすように調整"""
    if request.method == "POST":
        year_month_str = request.POST.get("year_month")
        holiday_input = request.POST.get("holiday_input", "")
        try:
            year, month = map(int, year_month_str.split("."))
        except ValueError:
            return JsonResponse({"error": "入力形式が正しくありません。YYYY.MM の形式で入力してください。"}, status=400)
        
        holidays = set(holiday_input.split(",")) if holiday_input else set()
        
        load_techs()
        first_day = datetime(year, month, 1)
        last_day = first_day.replace(day=calendar.monthrange(year, month)[1])
        date_list = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
        schedule = []
        alternating_week = (first_day.weekday() // 7) % 2 == 1  # 偶数週A, 奇数週B
        
    for date in date_list:
        weekday = date.weekday()
        if weekday==5:
            if get_team_for_saturday(base_saturday, weekday)=="B班":
                available_team = b_team 
                non_available_team = a_team
            else:
                available_team = a_team 
                non_available_team = b_team
            

        # 候補者の選定（明け休みや連続勤務を防ぐ）
        valid_catheter_candidates = [
            m for m in available_team if m in catheter_team
            and duty_count[m] < MAX_DUTY_CATHETER
            and (last_duty.get(m) is None or (date - last_duty[m]).days >= 2)
        ]
        valid_non_catheter_candidates = [
            m for m in available_team if m in non_catheter_team
            and duty_count[m] < MAX_DUTY_NON_CATHETER
            and (last_duty.get(m) is None or (date - last_duty[m]).days >= 2)
        ]

        # 当直者の決定（均等性を考慮）
        duty_catheter = min(valid_catheter_candidates, key=lambda x: duty_count[x], default="")
        duty_non_catheter = min(valid_non_catheter_candidates, key=lambda x: duty_count[x], default="")

        # 当直回数をカウントし、勤務日を記録
        if duty_catheter:
            duty_count[duty_catheter] += 1
            last_duty[duty_catheter] = date
        if duty_non_catheter:
            duty_count[duty_non_catheter] += 1
            last_duty[duty_non_catheter] = date

        # 日勤者の選定（祝日 or 日曜日）
        duty_day_shift = ""
        if str(date.date()) in holidays or weekday == 6:
            valid_day_candidates = [
                m for m in available_team if duty_count[m] < MAX_DUTY_NON_CATHETER
            ]
            duty_day_shift = min(valid_day_candidates, key=lambda x: duty_count[x], default="")

        # シフトデータを記録
        schedule.append([
        date.strftime('%Y-%m-%d'),
        duty_catheter if duty_catheter else "",  # nanを防ぐ
        duty_non_catheter if duty_non_catheter else "",  # nanを防ぐ
        duty_day_shift if duty_day_shift else ""  # nanを防ぐ
    ])
        # AB班の交代

        if weekday == 6:
            alternating_week = not alternating_week
            
    df = pd.DataFrame(schedule, columns=['日付', 'カテーテル可当直', 'カテーテル不可当直', '日勤'])
    df.to_csv(os.path.join('static', 'shift_schedule.csv'), index=False, encoding='utf-8-sig')
    
    return redirect("index")#これのせいで6日までしか作られない。ループが終わってしまう

   