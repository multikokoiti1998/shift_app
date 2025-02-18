from django.shortcuts import render, redirect
from django.http import JsonResponse
import pandas as pd
import os
import calendar
from datetime import datetime, timedelta
import random

TECHS_FILE = 'static/techs.csv'
AB_TEAMS_FILE = 'static/ab_teams.csv'
HOLIDAYS_FILE = 'static/holidays.csv'
SHIFT_FILE = 'static/shift_schedule.csv'
attendance_file='shift_manager\static\attendance_data.csv'


MAX_DUTY_CATHETER = 4
MAX_DUTY_NON_CATHETER = 2
MAX_DUTY_SUNDAY = 1

def load_techs():
    """技師データをロード"""
    global all_techs, catheter_team, non_catheter_team, a_team, b_team, duty_count, last_duty,duty_sunday
    all_techs, catheter_team, non_catheter_team, a_team, b_team = [], [], [], [], []
    duty_count = {}
    last_duty = {}
    duty_sunday={}
     

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
    duty_sunday={name: 0 for name in all_techs}

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

# 当直者の決定（均等性 + ランダム性を考慮）
def select_duty(candidates, duty_count):
    if not candidates:
        return ""  # 候補がいない場合は空文字

    # 最小の勤務回数を取得
    min_duty = min(duty_count[m] for m in candidates)

    # 最小の勤務回数のメンバーを抽出
    min_duty_candidates = [m for m in candidates if duty_count[m] == min_duty]

    # ランダムに 1 人選ぶ
    return random.choice(min_duty_candidates)

def create_shift_schedule(request):
    """シフトを作成し、制約を満たすように調整"""
    if request.method == "POST":
        year_month_str = request.POST.get("year_month")
        holiday_input = request.POST.get("holiday_input", "")
        year, month = map(int, year_month_str.split("."))
        holidays = set()

        if holiday_input:  # 入力がある場合のみ処理
            for date_str in holiday_input.split(","):  # ドットで分割
                try:
                    holidays.add(datetime.strptime(date_str.strip(), "%Y-%m-%d").date()) # `date` 型に変換
                except ValueError:
                    print(f"無効な日付フォーマット: {date_str}")  # エラーログ
        print(holidays)
        load_techs()
        base_saturday = "2025-01-04"
        first_day = datetime(year, month, 1)
        last_day = first_day.replace(day=calendar.monthrange(year, month)[1])
        date_list = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
        schedule = []

        # 日付情報をセッションに保存（generate_attendance_report で利用するため）
        request.session["shift_year"] = year
        request.session["shift_month"] = month
        request.session["holidays"] = [d.strftime('%Y-%m-%d') for d in holidays]
        
        
    for date in date_list:
        weekday = date.weekday()
        target_date = date.strftime("%Y-%m-%d")
        is_b_team = get_team_for_saturday(base_saturday, target_date) == "B班"

        match weekday:
            case 4:  # 金曜日
                available_team = b_team if not is_b_team else a_team
            case 5:  # 土曜日
                available_team = b_team if is_b_team else a_team
            case 6:  # 日曜日
                available_team = b_team if not is_b_team else a_team
            case _:  # 月～木
                available_team = a_team + b_team  # 全員対象
                

        # 候補者の選定（明け休みや連続勤務を防ぐ）
        valid_catheter_candidates = [
            m for m in available_team if m in catheter_team
            and duty_count[m] < MAX_DUTY_CATHETER
            and (last_duty.get(m) is None or (date - last_duty[m]).days >= 5)
        ]
        valid_non_catheter_candidates = [
            m for m in available_team if m in non_catheter_team
            and duty_count[m] < MAX_DUTY_NON_CATHETER
            and (last_duty.get(m) is None or (date - last_duty[m]).days >= 5)
        ]

        # 当直者の決定（均等性を考慮）
        duty_catheter = select_duty(valid_catheter_candidates, duty_count)

        duty_non_catheter = select_duty(valid_non_catheter_candidates, duty_count)
        
              # 日勤者の選定（祝日 or 日曜日）
        duty_day_catheter = ""
        if date.date() in holidays or weekday == 6:
            print(holidays)
            valid_day_candidates = [
                m for m in valid_non_catheter_candidates 
                if duty_sunday.get(m, 0) < MAX_DUTY_SUNDAY  # キーエラー防止
                and m != duty_catheter  # その日のカテーテル当直者ではない
                and m != duty_non_catheter  # その日の非カテーテル当直者ではない
            ]
            if valid_day_candidates:
                duty_day_catheter = select_duty(valid_day_candidates, duty_sunday)
        # 当直回数をカウントし、勤務日を記録
        if duty_catheter:
            duty_count[duty_catheter] += 1
            last_duty[duty_catheter] = date
        if duty_non_catheter:
            duty_count[duty_non_catheter] += 1
            last_duty[duty_non_catheter] = date
        # **日勤回数をカウント**
        if duty_day_catheter:
            duty_sunday[duty_day_catheter] += 1
            last_duty[duty_day_catheter]
        print(last_duty)#要確認

        # シフトデータを記録
        schedule.append([
        date.strftime('%Y-%m-%d'),
        duty_catheter if duty_catheter else "",  # nanを防ぐ
        duty_non_catheter if duty_non_catheter else "",  # nanを防ぐ
        duty_day_catheter if duty_day_catheter else ""  # nanを防ぐ
    ])

            
    df = pd.DataFrame(schedule, columns=['日付', 'カテーテル可当直', 'カテーテル不可当直', '日勤'])
    df.to_csv(os.path.join('static', 'shift_schedule.csv'), index=False, encoding='utf-8-sig')

    return redirect("index")

def load_shift_schedule():
    if os.path.exists(SHIFT_FILE):
        df_shift = pd.read_csv(SHIFT_FILE, encoding='utf-8-sig')
        df_shift['日付'] = pd.to_datetime(df_shift['日付'])
        return df_shift
    return pd.DataFrame()

def load_holidays():
    """祝日データを読み込む"""
    if os.path.exists(HOLIDAYS_FILE):
        df_holidays = pd.read_csv(HOLIDAYS_FILE, encoding='utf-8-sig')
        df_holidays['日付'] = pd.to_datetime(df_holidays['日付'])
        return set(df_holidays['日付'].dt.date)
    return set()

def load_ab_teams():
    """A/B班データを読み込む"""
    if os.path.exists(AB_TEAMS_FILE):
        df_teams = pd.read_csv(AB_TEAMS_FILE, encoding='utf-8-sig')
        a_team = df_teams[df_teams["班"] == "A"]["技師名"].tolist()
        b_team = df_teams[df_teams["班"] == "B"]["技師名"].tolist()
        return a_team, b_team
    return [], []

def load_shift_schedule():
    """当直・日勤データを読み込む"""
    if os.path.exists(SHIFT_FILE):
        df_shift = pd.read_csv(SHIFT_FILE, encoding='utf-8-sig')
        df_shift['日付'] = pd.to_datetime(df_shift['日付'])
        return df_shift
    return pd.DataFrame()

def generate_attendance_report(request):
    """ボタン押下で勤務表を生成"""
    year = request.session.get("shift_year", 2024)
    month = request.session.get("shift_month", 4)
    holidays = set(datetime.strptime(d, "%Y-%m-%d").date() for d in request.session.get("holidays", []))

    # 日付リストを生成
    start_date = datetime(year, month, 1)
    last_day = start_date.replace(day=calendar.monthrange(year, month)[1])
    dates = [start_date + timedelta(days=i) for i in range((last_day - start_date).days + 1)]

def get_team_for_saturday(base_saturday, target_date):
    #土曜日の出勤班を決定
    weeks_difference = (target_date - base_saturday).days // 7
    return "B班" if weeks_difference % 2 == 0 else "A班"

def generate_attendance_report(request):
    """ボタン押下で勤務表を生成"""
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2024, 4, 30)
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    holidays = load_holidays()
    a_team, b_team = load_ab_teams()
    shift_df = load_shift_schedule()
    base_saturday = "2025-01-04"

    output_data = []

    for _, row in pd.read_csv(attendance_file).iterrows():
        employee_id = row["社員ID"]
        name = row["氏名"]

        for date in dates:
            weekday = date.weekday()
            date_str = date.strftime('%Y-%m-%d')

            # 勤務判定
            if date.date() in holidays:
                work_status = "休み"
            elif weekday == 5:  # 土曜日
                team_for_saturday = get_team_for_saturday(base_saturday, date)
                work_status = "勤務" if (name in a_team and team_for_saturday == "A班") or (name in b_team and team_for_saturday == "B班") else "休み"
            elif weekday == 6:  # 日曜日
                work_status = "休み"
            else:
                work_status = "勤務"

            # シフトデータを確認
            duty_type = "なし"
            shift_match = shift_df[shift_df["日付"] == date_str]

            if not shift_match.empty:
                if name in shift_match["カテーテル可当直"].values:
                    duty_type = "当直"
                elif name in shift_match["カテーテル不可当直"].values:
                    duty_type = "当直"
                elif name in shift_match["日勤"].values:
                    duty_type = "日勤"

            output_data.append([
                employee_id, name, date_str, work_status, "なし", duty_type, "なし", "なし"
            ])

    output_df = pd.DataFrame(output_data, columns=["個人コード", "個人コード", "処理日", "カレンダー", "勤怠区分", "シフト区分", "出勤例外", "退勤例外"])
    
    output_file_path = os.path.join("static", "formatted_attendance.csv")
    output_df.to_csv(output_file_path, index=False, encoding='utf-8-sig')

    return JsonResponse({"message": "勤務表を生成しました", "file_url": "/static/formatted_attendance.csv"})