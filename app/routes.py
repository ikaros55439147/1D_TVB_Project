from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, url_for
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _, get_locale
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm,NewsSearchForm
from app.models import User, Post,News, NewsCategory,Content
from app.email import send_password_reset_email
# from utils.s3_upload import upload_to_s3
from flask_s3 import FlaskS3
import boto3
from botocore.exceptions import NoCredentialsError,ClientError
from urllib.parse import urlparse
import os
from app.config import AWSConfig
from werkzeug.utils import secure_filename
import hashlib
from sqlalchemy.exc import IntegrityError  # 处理数据库完整性错误
from sqlalchemy.orm import validates  
import uuid

s3_client = boto3.client('s3', region_name='ap-east-1') 


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('profile.html.j2', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])



def index():
    
    programs = get_program_data()
    image_key = 'images/'
    image_url = f"https://{AWSConfig.S3_BUCKET}.s3.{AWSConfig.AWS_REGION}.amazonaws.com/{image_key}"
    contents = Content.query.order_by(Content.created_at.desc()).limit(4).all()
    

    carousel_items = [
        {'image': 'ik1.jpg', 'title': '标题1', 'description': '描述1', 'active': True},
        {'image': 'ik2.jpg', 'title': '标题2', 'description': '描述2'},
        {'image': 'ik3.jpg', 'title': '标题3', 'description': '描述3'}
    ]

    

    return render_template('index.html.j2', carousel_items=carousel_items,
                        ikaros=("主标题", "副标题"),title=_('Home'), 
                           programs=programs,image_url=image_url,contents=contents)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'explore', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'explore', page=posts.prev_num) if posts.prev_num else None
    return render_template('index.html.j2', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html.j2', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html.j2', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html.j2',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html.j2', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('user.html.j2', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html.j2', title=_('Edit Profile'),
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('user', username=username))


# @app.route('/news')
# def news():
#     return render_template('news.j2', title='無線新聞')


@app.route('/entertainment')
def entertainment():
    
    programs = get_program_data()
    
    image_key = 'images/'
    image_url = f"https://{AWSConfig.S3_BUCKET}.s3.{AWSConfig.AWS_REGION}.amazonaws.com/{image_key}"
    

    entertainment_carousel_items = [
        {'image': 'ik1.jpg', 'title': '标题1', 'description': '描述1', 'active': True},
        {'image': 'ik2.jpg', 'title': '标题2', 'description': '描述2'},
        {'image': 'ik3.jpg', 'title': '标题3', 'description': '描述3'},
        {'image': 'ik4.jpg', 'title': '标题4', 'description': '描述4'},
        {'image': 'ik5.jpg', 'title': '标题5', 'description': '描述5'}
    ]

    

    return render_template('entertainment.html.j2', entertainment_carousel_items=entertainment_carousel_items,
                        ikaros=("主标题", "副标题"),title=_('entertainment'), programs=programs,image_url=image_url)

@app.route('/streaming')
def streaming():
    return render_template('streaming.html.j2', title='串流平台')

@app.route('/mytv_super')
def mytv_super():
    return render_template('mytv_super.html.j2', title='myTV SUPER')

@app.route('/tvb_anywhere')
def tvb_anywhere():
    return render_template('tvb_anywhere.html.j2', title='TVB Anywhere')

@app.route('/charity')
def charity():
    image_key = 'images/'
    image_url = f"https://{AWSConfig.S3_BUCKET}.s3.{AWSConfig.AWS_REGION}.amazonaws.com/{image_key}"
    
    return render_template('charity.html.j2', title='愛心基金',image_url=image_url)

@app.route('/program_schedule')
def program_schedule():
    return render_template('program_schedule.html.j2', title='節目表')

@app.route('/popular_programs')
def popular_programs():
    return render_template('popular_programs.html.j2', title='熱播焦點節目')

@app.route('/show_summaries')
def show_summaries():
    return render_template('show_summaries.html.j2', title='節目懶人包系列')

@app.route('/tvb_plus')
def tvb_plus():
    return render_template('tvb_plus.html.j2', title='TVB Plus')

@app.route('/pearl_channel')
def pearl_channel():
    return render_template('pearl_channel.html.j2', title='明珠台')

@app.route('/pearl_930')
def pearl_930():
    return render_template('pearl_930.html.j2', title='明珠930')



@app.route('/news')
def news():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    # 创建表单实例并设置分类选项
    form = NewsSearchForm()
    form.category.choices = [(0, '所有分类')] + [
        (c.id, c.name) for c in NewsCategory.query.all()
    ]
    
    # 查询逻辑
    query = News.query.order_by(News.publish_time.desc())
    if category_id and category_id > 0:
        query = query.filter_by(category_id=category_id)
        form.category.data = category_id
    
    pagination = query.paginate(page=page, per_page=10)
    
    return render_template('news.html.j2',
                        title='新闻中心',
                        form=form,
                        news=pagination.items,
                        pagination=pagination,
                        NewsCategory=NewsCategory)  # 传递模型类

@app.route('/news/<int:id>')
def news_detail(id):
    news_item = News.query.get_or_404(id)
    news_item.increment_views()  # 增加瀏覽量
    
    # 相關新聞推薦
    related_news = News.query.filter(
        News.category_id == news_item.category_id,
        News.id != news_item.id
    ).order_by(News.publish_time.desc()).limit(4).all()
    
    return render_template('news_detail.html.j2', 
                         title=news_item.title,
                         news=news_item,
                         related_news=related_news)

@app.route('/category/<category_name>')
def category_detail(category_name):
    # 获取分类下的所有内容
    page = request.args.get('page', 1, type=int)
    
    # 查询逻辑
    query = News.query.filter_by(category_name=category_name).order_by(News.publish_time.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    
    return render_template('category_detail.html.j2',
                         title=f'{category_name} - 分类详情',
                         category_name=category_name,
                         news=pagination.items,
                         pagination=pagination)

@app.route('/charity/activities')
def charity_activities():
    # 获取所有慈善活动
    page = request.args.get('page', 1, type=int)
    
    # 查询逻辑 - 假设有一个 CharityActivity 模型
    activities = CharityActivity.query.order_by(CharityActivity.publish_date.desc()).paginate(
        page=page, 
        per_page=12, 
        error_out=False
    )
    
    return render_template('charity_activities.html.j2',
                         title='愛心基金活動',
                         activities=activities.items,
                         pagination=activities)

# @app.route('/upload-news', methods=['POST'])
# def upload_news():
#     if 'image' in request.files:
#         image_url = upload_to_s3(request.files['image'], 'news_images')
#         news = News(
#             title=request.form['title'],
#             content=request.form['content'],
#             cover_image=image_url
#         )
#         db.session.add(news)
#         db.session.commit()
#     return redirect(url_for('news'))



# def get_s3_client():
#     return boto3.client(
#         's3',
#         aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
#         aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
#         region_name=app.config['S3_REGION']
#     )

# def get_s3_url(object_key):
#     """生成 S3 對象的 URL"""
#     s3_client = get_s3_client()
#     location = s3_client.get_bucket_location(Bucket=app.config['S3_BUCKET_NAME'])['LocationConstraint']
#     return f"https://{app.config['S3_BUCKET_NAME']}.s3.{location}.amazonaws.com/{object_key}"

# @app.route('/')
# def index():
#     try:
#         s3_client = get_s3_client()
        
#         # 獲取 S3 bucket 中的圖片列表 (假設在 'images' 文件夾下)
#         response = s3_client.list_objects_v2(
#             Bucket=app.config['S3_BUCKET_NAME'],
#             Prefix='images/'
#         )
        
#         images = []
#         if 'Contents' in response:
#             for obj in response['Contents']:
#                 if obj['Key'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
#                     images.append({
#                         'key': obj['Key'],
#                         'url': get_s3_url(obj['Key'])
#                     })
        
#         return render_template('index.html', images=images)
    
#     except NoCredentialsError:
#         return "AWS 憑證缺失或無效", 500
    

# def s3_to_https(s3_url):
#     """將 s3:// 路徑轉換為 HTTPS URL"""
#     if s3_url.startswith('s3://'):
#         parsed = urlparse(s3_url)
#         return f"https://{parsed.netloc}.s3.amazonaws.com{parsed.path}"
#     return s3_url  # 如果不是 S3 路徑則原樣返回

# @app.route('/')
# def home():
#     # 假設的輪播數據（可從資料庫或 API 取得）
#     carousel_items = [
#         {
#             "image": "s3://mytvbprojectbucket-oj/伊/102402954_p0_master1200.jpg",
#             "title": "標題 1",
#             "description": "這是第一張圖片的說明",
#             "active": True  # 預設顯示第一張
#         },
#         {
#             "image": "s3://mytvbprojectbucket-oj/伊/103849283_p0_master1200.jpg",
#             "title": "標題 2",
#             "description": "這是第二張圖片的說明",
#             "active": False
#         },
#         {
#             "image": "s3://mytvbprojectbucket-oj/伊/103882005_p2_master1200.jpg",
#             "title": "標題 3",
#             "description": "這是第三張圖片的說明",
#             "active": False
#         }
#     ]

#     for item in carousel_items:
#         item['image_url'] = s3_to_https(item['image'])

#     return render_template('index.html.j2', carousel_items=carousel_items)


# @app.route('/', methods=['GET', 'POST'])
# @app.route('/index', methods=['GET', 'POST'])
# @login_required
# def index():
#     form = PostForm()
    
#     # 处理发帖逻辑
#     if form.validate_on_submit():
#         post = Post(body=form.post.data, author=current_user)
#         db.session.add(post)
#         db.session.commit()
#         flash(_('Your post is now live!'))
#         return redirect(url_for('index'))
    
#     # 获取分页帖子
#     page = request.args.get('page', 1, type=int)
#     posts = current_user.followed_posts().paginate(
#         page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    
#     # 获取S3图片
#     images = []
#     try:
#         s3_client = get_s3_client()
#         response = s3_client.list_objects_v2(
#             Bucket=app.config['S3_BUCKET_NAME'],
#             Prefix='images/'
#         )
        
#         if 'Contents' in response:
#             for obj in response['Contents']:
#                 if obj['Key'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
#                     images.append({
#                         'key': obj['Key'],
#                         'url': get_s3_url(obj['Key'])
#                     })
#     except NoCredentialsError:
#         flash(_('AWS credentials are missing or invalid'), 'error')
    
#     # 渲染模板
#     return render_template(
#         'index.html.j2', 
#         title=_('Home'), 
#         form=form,
#         posts=posts.items, 
#         images=images,
#         next_url=url_for('index', page=posts.next_num) if posts.next_num else None,
#         prev_url=url_for('index', page=posts.prev_num) if posts.prev_num else None
#     )

def get_program_data():
    """获取节目数据"""
    programs = []
    image_dir = os.path.join(app.static_folder, 'app', 'images')
    
    for i in range(1, 10):
        programs.append({
            'id': i,
            'name': f'節目 {chr(64+i)}',
            'image': f'ik{i}.jpg' if os.path.exists(os.path.join(image_dir, f'ik{i}.jpg')) else 'default.jpg'
        })
    return programs



@app.route('/upload_s3', methods=['GET', 'POST'])
def upload_s3():
    if request.method == 'POST':
        # 檢查是否有文件被上傳
        if 'file' not in request.files:
            return '沒有選擇文件'
        
        file = request.files['file']
        
        # 檢查文件名是否合法
        if file.filename == '':
            return '未選擇文件'
        
        if file:
            # 安全處理文件名
            file_hash = hashlib.sha256(file.read()).hexdigest()
            file.seek(0)  # 重置文件指針
            filename = f"{file_hash}_{secure_filename(file.filename)}"
            
            try:
                # 上傳文件到 S3
                AWSConfig.s3_client.upload_fileobj(
                    file,
                    AWSConfig.S3_BUCKET,
                    f"uploads/{filename}"  # 指定存儲路徑
                )
                return redirect(url_for('upload_success', filename=filename))
            except NoCredentialsError:
                return 'AWS 憑證未配置'
            except Exception as e:
                return f'上傳失敗: {str(e)}'
    
    return render_template('upload_s3.html.j2',title='upload S3')
# def upload_success(filename):
#     return f'文件 {filename} 上傳成功！'


@app.template_filter('time_ago')
def time_ago_filter(dt):
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365}年前"
    if diff.days > 30:
        return f"{diff.days // 30}個月前"
    if diff.days > 0:
        return f"{diff.days}天前"
    if diff.seconds > 3600:
        return f"{diff.seconds // 3600}小時前"
    if diff.seconds > 60:
        return f"{diff.seconds // 60}分鐘前"
    return "剛剛"

# 註冊過濾器
app.jinja_env.filters['time_ago'] = time_ago_filter


@app.route('/admin')
def admin():
    contents = Content.query.order_by(Content.created_at.desc()).all()
    return render_template('admin.html.j2', contents=contents)

@app.route('/create-content', methods=['POST'])
def create_content():
    try:
        # 獲取表單數據
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image = request.files.get('image')

        # 驗證必填字段
        if not all([title, description, image]):
            flash('所有字段均为必填项', 'danger')
            return redirect(url_for('admin'))

        # 驗證圖片
        if not allowed_file(image.filename):
            flash('僅支持 JPG/PNG 格式的圖片', 'danger')
            return redirect(url_for('admin'))

        # 生成唯一文件名並上傳S3
        file_ext = secure_filename(image.filename).rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        s3_key = f"uploads/{unique_filename}"

        s3_client.upload_fileobj(
            image,
            app.config['S3_BUCKET'],
            s3_key,
            ExtraArgs={
                'ContentType': image.content_type,
                'ACL': 'public-read'
            }
        )

        # 構建S3公開URL
        s3_url = f"https://mytvbprojectbucket-1.s3.ap-east-1.amazonaws.com/{s3_key}"

        # 創建數據庫記錄
        new_content = Content(
            title=title,
            description=description,
            image_path=s3_url
        )

        db.session.add(new_content)
        db.session.commit()
        flash('內容新增成功！', 'success')

    except IntegrityError:
        db.session.rollback()
        flash('標題已存在，請使用唯一標題', 'danger')
    except ClientError as e:
        db.session.rollback()
        app.logger.error(f"S3上傳失敗: {e}")
        flash('文件上傳失敗，請檢查權限或稍後再試', 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"系統錯誤: {e}")
        flash('系統錯誤，請稍後再試', 'danger')

    return redirect(url_for('admin'))

@app.route('/delete-content/<int:id>', methods=['POST'])
def delete_content(id):
    content = Content.query.get_or_404(id)
    try:
        # 從S3刪除文件（可選）
        # s3_client.delete_object(Bucket=app.config['S3_BUCKET'], Key=...)
        
        db.session.delete(content)
        db.session.commit()
        flash('內容已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('刪除失敗', 'danger')
    return redirect(url_for('admin'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS