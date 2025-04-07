// 新聞搜索表單提交
document.querySelector('.news-filter form').addEventListener('submit', function(e) {
    const keyword = document.querySelector('#keyword').value.trim();
    const category = document.querySelector('#category').value;
    
    // 如果沒有搜索關鍵字和分類選擇，阻止表單提交
    if (!keyword && category === '0') {
        e.preventDefault();
        // 可以添加提示信息
        alert('請輸入搜索關鍵字或選擇分類');
    }
});

// 圖片懶加載
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = [].slice.call(document.querySelectorAll('img.lazy'));
    
    if ('IntersectionObserver' in window) {
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.classList.remove('lazy');
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });
        
        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    }
});