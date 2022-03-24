from mixer.backend.sqlalchemy import Mixer
from mixer.main import LOGGER


class AsyncProxyMixer:
    def __init__(self, mixer, count=5, guards=None):
        self.count = count
        self.mixer = mixer
        self.guards = guards

    async def blend(self, scheme, **values):
        if self.guards:
            return await self.mixer._guard(scheme, self.guards, **values)

        return [
            await self.mixer.blend(scheme, **values) for _ in range(self.count)
        ]


class AsyncMixer(Mixer):
    async def _postprocess(self, target):
        if self.params.get('commit'):
            session = self.params.get('session')
            if not session:
                LOGGER.warning(
                    "'commit' set true but session not initialized.")
            else:
                session.add(target)
                await session.commit()

        return target

    def postprocess(self, target):
        return self._postprocess(target)

    def cycle(self, count=5):
        return AsyncProxyMixer(self, count)
