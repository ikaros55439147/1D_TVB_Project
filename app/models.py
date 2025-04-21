
from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, db, login
import jwt
from sqlalchemy.orm import validates  # 新增导入

from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, followers.c.followed_id == Post.user_id
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({"reset_password": self.id,
                           "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)},
                          app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")[
                "reset_password"]
        except:           
            return None
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Post {self.body}>'
    
class NewsCategory(db.Model):
    __tablename__ = 'news_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    
    # 与News模型的关系
    news = db.relationship('News', backref='category', lazy='dynamic')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    summary = db.Column(db.String(300))
    cover_image = db.Column(db.String(200))
    publish_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('news_category.id'))
    
    def increment_views(self):
        self.views += 1
        db.session.commit()

class CharityActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)


    # 在原有 models.py 基础上新增以下模型：

# --------------------- 新增节目相关模块 ---------------------
class ProgramSchedule(db.Model):
    """节目时间表"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True)
    start_time = db.Column(db.DateTime, index=True)
    end_time = db.Column(db.DateTime)
    channel = db.Column(db.String(50))  # 播放频道
    episode = db.Column(db.String(30))  # 第几集
    is_repeat = db.Column(db.Boolean, default=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))

class Program(db.Model):
    """节目详情"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    genre = db.Column(db.String(50))  # 节目类型
    total_episodes = db.Column(db.Integer)
    thumbnail = db.Column(db.String(200))
    schedules = db.relationship('ProgramSchedule', backref='program', lazy='dynamic')

# --------------------- 用户互动模块 ---------------------
class Comment(db.Model):
    """用户评论"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))

class Rating(db.Model):
    """节目评分"""
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float)  # 1-5分
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))

class WatchHistory(db.Model):
    """观看历史"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
    watch_time = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer)  # 观看时长（秒）

# --------------------- 运营管理模块 ---------------------
class Advertisement(db.Model):
    """广告管理"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    position = db.Column(db.String(50))  # 广告位标识
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    click_count = db.Column(db.Integer, default=0)

class LiveChannel(db.Model):
    """直播频道"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    stream_url = db.Column(db.String(200))
    current_program = db.Column(db.String(120))
    viewers = db.Column(db.Integer, default=0)

# --------------------- 会员服务模块 ---------------------
class SubscriptionPlan(db.Model):
    """订阅套餐"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # 套餐名称
    price = db.Column(db.Float)
    duration = db.Column(db.Integer)  # 套餐天数
    features = db.Column(db.Text)  # JSON格式存储特权

class UserSubscription(db.Model):
    """用户订阅记录"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

# --------------------- 内容管理模块 ---------------------
class Episode(db.Model):
    """剧集详情"""
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
    episode_number = db.Column(db.Integer)
    title = db.Column(db.String(120))
    video_url = db.Column(db.String(200))
    duration = db.Column(db.Integer)  # 视频时长（秒）

class Talent(db.Model):
    """艺人资料"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    bio = db.Column(db.Text)
    birthdate = db.Column(db.Date)
    profile_image = db.Column(db.String(200))
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))  # 代表作品


class Content(db.Model):
    __tablename__ = 'content'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    image_path = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Content {self.title}>'
    
    # def Descriptive_Chart(self):
