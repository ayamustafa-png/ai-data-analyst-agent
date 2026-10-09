import os
import pandas as pd
import gradio as gr
from google import genai
from agent.agent import run_agent as run_data_analyst_agent
from dotenv import load_dotenv

# إعادة تحميل ملف .env وتجاوز أي متغير قديم
load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

# إنشاء الـ Client بالمفتاح مباشرة
client = genai.Client(api_key=api_key)

# 1. إعداد الـ Client والدالة الخاصة بـ Gemini LLM
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

def gemini_llm(prompt):
    # استخدام الموديل الموصى به مباشرة من رسالة الخطأ مع خيارات بديلة من قائمتك
    models_to_try = [
        'gemini-3.8-flash',
        'gemini-3.5-flash',
        'gemini-flash-latest'
    ]
    
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            last_error = e
            continue
            
    raise last_error

def analyze_dataset(file_obj, user_query):
    # 1. التحقق من وجود الملف والسؤال
    if file_obj is None:
        return "⚠️ الرجاء رفع ملف CSV أولاً.", None
    if not user_query or not user_query.strip():
        return "⚠️ الرجاء كتابة السؤال أو التحليل المطلوب.", None

    csv_path = file_obj.name

    try:
        # قراءة الملف
        df = pd.read_csv(csv_path)

        # 2. تشغيل الـ Agent
        res = run_data_analyst_agent(
            question=user_query,
            df=df,
            llm=gemini_llm
        )

        # 3. معالجة النتيجة بذكاء لتفادي ظهور None
        explanation = None

        if isinstance(res, dict):
            explanation = res.get('explanation') or res.get('result') or res.get('answer') or res.get('output')
        else:
            explanation = (
                getattr(res, 'explanation', None) or 
                getattr(res, 'result', None) or 
                getattr(res, 'answer', None) or 
                getattr(res, 'output', None) or 
                str(res)
            )

        if not explanation or str(explanation).strip() == "None":
            explanation = "تم تنفيذ التحليل بنجاح."

        # 4. التأكد من الرسم البياني
        chart_path = "output_chart.png"
        chart_output = None

        if isinstance(res, dict) and res.get('charts'):
            chart_output = res['charts'][0]
        elif hasattr(res, 'charts') and getattr(res, 'charts'):
            chart_output = getattr(res, 'charts')[0]
        elif os.path.exists(chart_path):
            chart_output = chart_path

        return str(explanation), chart_output

    except Exception as e:
        return f"❌ حدث خطأ أثناء تشغيل الـ Agent: {str(e)}", None
# 🎨 بناء واجهة المستخدم بـ Gradio
with gr.Blocks(title="AI Data Analyst Agent") as demo:
    gr.Markdown(
        """
        # 📊 AI Data Analyst Agent
        رفع ملف الـ CSV وطرح أسئلة البزنس/التحليل المطلوب. يقوم الـ Agent بفحص البيانات، كتابة كود Pandas، وتنفيذ الرسم البياني تلقائياً.
        """
    )

    with gr.Row():
        # العمود الأيسر: المدخلات
        with gr.Column(scale=1):
            file_input = gr.File(label="📁 رفع ملف CSV", file_types=[".csv"])
            query_input = gr.Textbox(
                label="💬 السؤال أو التحليل المطلوب",
                placeholder="مثال: ما هي أكثر 5 منتجات مبيعاً؟ مع رسم بياني للنتائج.",
                lines=3
            )
            submit_btn = gr.Button("تطبيق التحليل 🚀", variant="primary")

        # العمود الأيمن: المخرجات
        with gr.Column(scale=1):
            text_output = gr.Textbox(label="📋 التقرير والنتائج", lines=12)
            image_output = gr.Image(label="📈 الرسم البياني الناتج")

    # ربط زر التفاعل بالدالة
    submit_btn.click(
        fn=analyze_dataset,
        inputs=[file_input, query_input],
        outputs=[text_output, image_output]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())