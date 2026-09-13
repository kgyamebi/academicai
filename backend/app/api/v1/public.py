from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.app_cache import cache_get, cache_set
from app.db.session import get_db, get_db_read
from app.models.admin import AnalyticsEvent
from app.models.content import FAQ, BlogPost, SeoPage
from app.schemas.common import AnalyticsIn

_PUBLIC_TTL_SECONDS = 60

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/seo/{slug}")
def seo_page(slug: str, db: Session = Depends(get_db_read)):
    page = db.scalar(select(SeoPage).where(SeoPage.slug == slug, SeoPage.is_published.is_(True)))
    if not page:
        raise HTTPException(404, "Page not found.")
    return {
        "slug": page.slug,
        "title": page.title,
        "meta_description": page.meta_description,
        "heading": page.heading,
        "body_markdown": page.body_markdown,
        "canonical_path": page.canonical_path,
    }


@router.get("/blog")
def blog_index(db: Session = Depends(get_db_read)):
    cached = cache_get("public:blog")
    if cached is not None:
        return cached
    posts = db.scalars(
        select(BlogPost)
        .where(BlogPost.is_published.is_(True))
        .order_by(BlogPost.published_at.desc())
        .limit(50)
    ).all()
    payload = {
        "items": [
            {"slug": p.slug, "title": p.title, "excerpt": p.excerpt, "published_at": p.published_at.isoformat() if p.published_at else None}
            for p in posts
        ]
    }
    cache_set("public:blog", payload, _PUBLIC_TTL_SECONDS)
    return payload


@router.get("/blog/{slug}")
def blog_post(slug: str, db: Session = Depends(get_db_read)):
    post = db.scalar(select(BlogPost).where(BlogPost.slug == slug, BlogPost.is_published.is_(True)))
    if not post:
        raise HTTPException(404, "Post not found.")
    return {"slug": post.slug, "title": post.title, "excerpt": post.excerpt, "body_markdown": post.body_markdown, "author": post.author}


@router.get("/faqs")
def faqs(db: Session = Depends(get_db_read)):
    cached = cache_get("public:faqs")
    if cached is not None:
        return cached
    items = db.scalars(select(FAQ).where(FAQ.is_published.is_(True)).order_by(FAQ.sort_order).limit(100)).all()
    payload = {"items": [{"question": f.question, "answer": f.answer, "category": f.category} for f in items]}
    cache_set("public:faqs", payload, _PUBLIC_TTL_SECONDS)
    return payload


@router.post("/analytics")
def track(payload: AnalyticsIn, db: Session = Depends(get_db)):
    # Never accept assignment text in analytics properties.
    safe_props = {k: v for k, v in payload.properties.items() if k not in {"text", "document", "assignment", "content"}}
    db.add(AnalyticsEvent(event_name=payload.event_name[:80], path=payload.path, properties=str(safe_props)[:2000]))
    db.commit()
    return {"ok": True}
