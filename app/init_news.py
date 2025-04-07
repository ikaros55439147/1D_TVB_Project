from app import app, db
from app.models import NewsCategory, News
from datetime import datetime, timedelta

def init_news_data():
    with app.app_context():
        # 創建新聞分類
        categories = ['時事', '財經', '娛樂', '體育', '科技']
        for name in categories:
            if not NewsCategory.query.filter_by(name=name).first():
                category = NewsCategory(name=name)
                db.session.add(category)
        
        db.session.commit()
        
        # 創建示例新聞
        if News.query.count() == 0:
            categories = NewsCategory.query.all()
            for i in range(1, 31):
                category = categories[i % len(categories)]
                news = News(
                    title=f"示例新聞標題 {i}",
                    summary=f"這是示例新聞 {i} 的摘要內容，簡要描述新聞的主要內容。",
                    content=f"<p>這是示例新聞 {i} 的詳細內容。</p><p>這裡可以包含多段落的詳細新聞報導。</p>",
                    cover_image=f"https://picsum.photos/800/450?random={i}",
                    publish_time=datetime.utcnow() - timedelta(days=i),
                    views=i * 10,
                    is_featured=i % 5 == 0,
                    category=category
                )
                db.session.add