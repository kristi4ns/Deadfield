import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from api import db

API_FOLDER = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Deadfield")

# CSS fails tiek atdots no /static, bet lapa tiek izveidota no veidnes mapē templates
app.mount("/static", StaticFiles(directory=os.path.join(API_FOLDER, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(API_FOLDER, "templates"))

# Izveido tabulu, kad serveris startē
db.create_tables()


class ScoreIn(BaseModel):
    # Šis apraksta, ko spēlei jānosūta uz POST /scores
    # Ja dati neder, FastAPI atbild ar 422 un nekas netiek saglabāts

    # Atstarpes vārda sākumā un beigās tiek noņemtas pirms pārbaudēm
    model_config = ConfigDict(str_strip_whitespace=True)

    # No 1 līdz 12 simboliem: burti, cipari, atstarpes un _ - . (tāpat kā spēlē)
    name: str = Field(min_length=1, max_length=12, pattern=r"^[\w .\-]+$")

    # Punkti nedrīkst būt negatīvi
    points: int = Field(ge=0, le=10_000_000)


# ---------- REST API ----------
@app.post("/scores", status_code=201)
def save_score(score: ScoreIn):
    db.add_score(score.name, score.points)
    return {"name": score.name, "points": score.points}


@app.get("/scores/top")
def get_top_scores():
    return db.get_top_scores(10)


@app.get("/players/{name}/stats")
def get_player_stats(name: str):
    stats = db.get_player_stats(name)

    if stats is None:
        raise HTTPException(status_code=404, detail="Player not found")

    return stats


# ---------- Mājaslapa ----------
def show_page(request, page, title, extra_data=None):
    # Visas lapas izmanto vienu veidni (base.html)
    # Vērtība "page" pasaka veidnei, kuru lapu rādīt
    context = {"page": page, "title": title}
    if extra_data:
        context.update(extra_data)

    return templates.TemplateResponse(request=request, name="base.html", context=context)


@app.get("/", response_class=HTMLResponse)
def leaderboard_page(request: Request):
    scores = db.get_top_scores(10)
    return show_page(request, "leaderboard", "Līderu tabula", {"scores": scores})


@app.get("/players/{name}", response_class=HTMLResponse)
def player_page(request: Request, name: str):
    stats = db.get_player_stats(name)

    # Spēlētāja nav, tāpēc atbilde ir 404
    if stats is None:
        raise HTTPException(status_code=404, detail="Player not found")

    return show_page(request, "player", stats["name"], {"stats": stats})


@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return show_page(request, "about", "Par spēli")