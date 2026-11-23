import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(sender_email, sender_password, recipient_email, subject, body, pdf_paths):
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach the email body
        msg.attach(MIMEText(body, 'html'))

        # Attach each PDF file
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_path)}")
                    msg.attach(part)
            else:
                print(f"Warning: The file {pdf_path} does not exist and will not be attached.")

        # Connect to the SMTP server and send the email
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")

if __name__ == "__main__":
    # Email credentials
    sender_email = "naishashelke@gmail.com"
    sender_password = "mmvt lbjv pwqi crvw"  # Use an App Password if 2FA is enabled

    # Email content
    subject = "Research Internship Application-2025"
    body = """
    <p>Dear Sir/Ma’am,<br><br>

    My name is <b>Naisha</b>, and I am a final-year B.Tech student in Information Science Engineering (specializing in AI and Robotics) at Presidency University, Bangalore, India. I am writing to express my keen interest in joining your research group as a research intern through the TEEP @ AsiaPlus 2025 program.<br><br>

    My primary interests lie in <b>Artificial Intelligence, Intelligent Systems, Smart Manufacturing, and Smart Healthcare</b> — areas that closely align with your research expertise.<br><br>

    During my academic journey, I have gained significant experience through diverse internships and research projects. Notably:<br><br>

    - <b>Software Intern at Bharat Electronics Limited</b> – Built a modern AI-based PDF summarizer and designed a user-friendly web interface using contemporary front-end tools.<br>
    - <b>Automation Engineer at LG Soft India</b> – Conducted functional, automation, regression, and system testing, collaborating with cross-functional teams to enhance smart TV software quality.<br><br>

    Additionally, I have led projects such as:<br><br>

    - <b>Raspberry Pi-based smart water prediction system</b> using IoT sensors and Python algorithms for sustainable agriculture in highland regions.<br>
    - <b>AI-powered object detection models</b> using CNNs for smart surveillance applications.<br>
    - <b>AI chatbot for e-commerce</b> integrated with Angular, Spring Boot, and MySQL, showcasing my passion for building scalable, high-performance solutions aligned with Industry 4.0 goals.<br><br>

    I am highly motivated to apply my technical expertise and international research experience to contribute to your ongoing projects.<u> I am also planning to pursue my Master’s degree after the internship, and if selected, I would love to continue my Master’s studies at the same university, building upon the research and mentorship experience gained during the internship.</u><br><br>

    <i>Furthermore, if there are no positions currently available under the TEEP program, I would be extremely grateful if you could kindly consider inviting me to join your research group through any other suitable arrangement with some stipend support. I am confident in my skills and dedication, and I believe I can make valuable contributions to your projects</i>.<br><br>

    I have attached my CV and other supporting documents for your kind consideration. I would be honored to contribute to your research initiatives and learn under your esteemed mentorship.<br><br>

    Thank you very much for your time and consideration. I look forward to the opportunity of working with you.<br><br>

    Sincerely,<br>
    Naisha<br>
    B.Tech – Information Science Engineering<br>
    Presidency University, Bangalore<br>
    naishashelke@gmail.com
    </p>
    """

    # List of recipients and their respective PDF attachments
    recipients = [
        ("rishabh89003@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf",]),
        ("rish89003@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf",]),
        ("yinzx@stust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("cwlung@asia.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("gcchen0330@dragon.nchu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("lanchiwei@saturn.yzu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("iqbal.marjan@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yfwang@cycu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("gialinhh97@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("hllu@mail.dyu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("ieewnl@ccu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("arunks@yuntech.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("khchen@cc.ncue.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("cltung2010@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jyhcheng2010@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("indkrisur11@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chanhl@mail.cgu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("oswaldchuang@mail.ncku.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yien@saturn.yzu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("mjchern@ntust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),#NTUST
        ("thyangza@gs.ncku.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("isackf@saturn.yzu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        #("admcarol@ccu.edu.tw", ["cover.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),#CCU ARVIND
        ("hclin@ncut.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("ihsan@saturn.yzu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jasonshih@stust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yttsai@saturn.yzu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        #("azaharu.23@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("phkuo@ccu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),#CCU
        ("hchuang@ccu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),#CCU
        ("lwliao@gm.nutc.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("saeedvand@ntnu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chen2024@pu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chen2336646@hotmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("girish@nycu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yushenglin@stust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("hcshih@saturn.yzu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("dgliu@fcu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("imbj92@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("4B2Yu002@stust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yuhsiang@ntu.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("kheanthye@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("pan.minc@g.ncu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("sywan@mail.cgu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("ccchang@cc.ncue.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("bbgupta@asia.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("icwey@mail.cgu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("wc.lin@mail.nsysu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("wcl27cam@gmail.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("mchu@ntu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jennytzou@quantavision.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jyeyutzou@gmail.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("qainbeihong@stust.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("changkm@nkust.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("R1342011@ems.niu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("pksahoo@mail.cgu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("cwsacws@saturn.yzu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("hllu@mail.dyu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chenju.lin@saturn.yzu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chantalh@ncut.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("nliou@stust.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("tsching@nchu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("ptluan@hcmus.edu.vn",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("abdulshabir@outlook.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("taukir.alam007@gmail.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("huangcy@yuntech.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("wry87c@cc.ncue.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("schuang@mail.ntut.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("han.hsiang@mail.ntut.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("ytwang@mail.tku.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("siyang4301@gmail.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yinzx@stust.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chingchun@nycu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("tingyuan@mail.ncku.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("hmchen@mail.fcu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jhsu@ntnu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("stliong@o365.fcu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("pclin@saturn.yzu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("kjfann@nchu.edu.tw",["cover.pdf","LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chenh2@ntnu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("syc@must.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("caw@must.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yien@saturn.yzu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("junehsu@gs.ncku.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jh.lee@gapp.nthu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("thyangza@gs.ncku.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("plyen@ntu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("r08631048@ntu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("kittyc@stust.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("sofin@nycu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("sanjaya.sanjaya5@gmail.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("kemo@stust.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("ugo.roux31@gmail.com",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("alvisfong@wmich.edu",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("cwchou@fcu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yllai@cc.ncue.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("chengch@fcu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("sheanjen@nycu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("smallpig@widelab.org",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("rachel@ccu.edu.tw",["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("yangct@mail.ncku.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("cweiwang@mail.ntust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("mjchern@ntust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("jsleu@mail.ntust.edu.tw", ["LOR_merged.pdf","Naisha_CV.pdf"]),
        ("siyang4301@gmail.com", ["LOR_merged.pdf","Naisha_CV.pdf"])
    ]
    for recipient_email, pdf_paths in recipients:
        send_email(sender_email, sender_password, recipient_email, subject, body, pdf_paths)

    '''("yinzx@stust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("gcchen0330@dragon.nchu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("lanchiwei@saturn.yzu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("iqbal.marjan@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yfwang@cycu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("gialinhh97@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("hllu@mail.dyu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("ieewnl@ccu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("arunks@yuntech.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("khchen@cc.ncue.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("cltung2010@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jyhcheng2010@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("indkrisur11@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chanhl@mail.cgu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("oswaldchuang@mail.ncku.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yien@saturn.yzu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("mjchern@ntust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),#NTUST
        ("thyangza@gs.ncku.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("isackf@saturn.yzu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        #("admcarol@ccu.edu.tw", ["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),#CCU ARVIND
        ("hclin@ncut.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("ihsan@saturn.yzu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jasonshih@stust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yttsai@saturn.yzu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("azaharu.23@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("phkuo@ccu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),#CCU
        ("hchuang@ccu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),#CCU
        ("lwliao@gm.nutc.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("saeedvand@ntnu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chen2024@pu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chen2336646@hotmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("girish@nycu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yushenglin@stust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("hcshih@saturn.yzu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("dgliu@fcu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("imbj92@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("4B2Yu002@stust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yuhsiang@ntu.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("kheanthye@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),

        ("pan.minc@g.ncu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("sywan@mail.cgu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("ccchang@cc.ncue.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("bbgupta@asia.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("icwey@mail.cgu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("wc.lin@mail.nsysu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("wcl27cam@gmail.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("mchu@ntu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jennytzou@quantavision.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jyeyutzou@gmail.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("qainbeihong@stust.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("changkm@nkust.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("R1342011@ems.niu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("pksahoo@mail.cgu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("cwsacws@saturn.yzu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("hllu@mail.dyu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chenju.lin@saturn.yzu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chantalh@ncut.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("nliou@stust.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("tsching@nchu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("ptluan@hcmus.edu.vn",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("abdulshabir@outlook.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("taukir.alam007@gmail.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("huangcy@yuntech.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("wry87c@cc.ncue.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("schuang@mail.ntut.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("han.hsiang@mail.ntut.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("ytwang@mail.tku.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("siyang4301@gmail.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yinzx@stust.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chingchun@nycu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("tingyuan@mail.ncku.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("hmchen@mail.fcu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jhsu@ntnu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("stliong@o365.fcu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("pclin@saturn.yzu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("kjfann@nchu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chenh2@ntnu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("syc@must.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("caw@must.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yien@saturn.yzu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("junehsu@gs.ncku.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jh.lee@gapp.nthu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("thyangza@gs.ncku.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("plyen@ntu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("r08631048@ntu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("kittyc@stust.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("sofin@nycu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("sanjaya.sanjaya5@gmail.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("kemo@stust.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("ugo.roux31@gmail.com",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("alvisfong@wmich.edu",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("cwchou@fcu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("yllai@cc.ncue.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("chengch@fcu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("sheanjen@nycu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("smallpig@widelab.org",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("rachel@ccu.edu.tw",["RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"])
        ("yangct@mail.ncku.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("cweiwang@mail.ntust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("mjchern@ntust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("jsleu@mail.ntust.edu.tw", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),
        ("siyang4301@gmail.com", ["Research Plan24.pdf","RISH_IIPP_RESUME.pdf","Rishabh_LOR.pdf"]),'''