# -*- coding: utf-8 -*-
"""Saqlash: Upstash Redis (REDIS_URL bo'lsa) yoki xotira."""
import json
import logging
import os

log = logging.getLogger("storage")
PREFIX = "bunker:"


class Storage:
    def __init__(self):
        self.r = None
        self.mem = {}
        url = os.getenv("REDIS_URL") or os.getenv("UPSTASH_REDIS_URL")
        if url:
            try:
                import redis.asyncio as redis
                self.r = redis.from_url(url, decode_responses=True)
            except Exception as e:  # pragma: no cover
                log.warning("Redis ulanmadi: %s", e)

    # ------------------------------------------------ o'yinlar
    async def save_game(self, g):
        data = json.dumps(g.to_dict(), ensure_ascii=False)
        if self.r:
            try:
                await self.r.set(PREFIX + "game:" + g.id, data, ex=60 * 60 * 24)
                return
            except Exception as e:
                log.warning("save_game: %s", e)
        self.mem["game:" + g.id] = data

    async def delete_game(self, gid):
        if self.r:
            try:
                await self.r.delete(PREFIX + "game:" + gid)
            except Exception as e:
                log.warning("delete_game: %s", e)
        self.mem.pop("game:" + gid, None)

    async def load_games(self):
        out = []
        if self.r:
            try:
                async for key in self.r.scan_iter(PREFIX + "game:*"):
                    v = await self.r.get(key)
                    if v:
                        out.append(json.loads(v))
            except Exception as e:
                log.warning("load_games: %s", e)
        return out

    # ------------------------------------------------ statistika
    async def add_stats(self, uid, name, played=1, bunker=0, survived=0):
        key = PREFIX + "u:" + str(uid)
        if self.r:
            try:
                p = self.r.pipeline()
                p.hset(key, "name", name)
                p.hincrby(key, "played", played)
                p.hincrby(key, "bunker", bunker)
                p.hincrby(key, "survived", survived)
                if bunker:
                    p.zincrby(PREFIX + "top", bunker, str(uid))
                await p.execute()
                return
            except Exception as e:
                log.warning("add_stats: %s", e)
        d = self.mem.setdefault(key, {"name": name, "played": 0, "bunker": 0, "survived": 0})
        d["name"] = name
        d["played"] += played
        d["bunker"] += bunker
        d["survived"] += survived
        top = self.mem.setdefault("top", {})
        top[str(uid)] = top.get(str(uid), 0) + bunker

    async def get_stats(self, uid):
        key = PREFIX + "u:" + str(uid)
        if self.r:
            try:
                d = await self.r.hgetall(key)
                return {k: (int(v) if k != "name" else v) for k, v in d.items()} if d else None
            except Exception as e:
                log.warning("get_stats: %s", e)
        return self.mem.get(key)

    async def top(self, n=10):
        if self.r:
            try:
                rows = await self.r.zrevrange(PREFIX + "top", 0, n - 1, withscores=True)
                out = []
                for uid, sc in rows:
                    name = await self.r.hget(PREFIX + "u:" + uid, "name")
                    out.append((name or "?", int(sc)))
                return out
            except Exception as e:
                log.warning("top: %s", e)
        top = self.mem.get("top", {})
        rows = sorted(top.items(), key=lambda x: -x[1])[:n]
        return [(self.mem.get(PREFIX + "u:" + u, {}).get("name", "?"), s) for u, s in rows]
