
from fastapi import APIRouter
from sources.schemas.hello_world import HelloWorldModel

__all__ = (
    'router',
)


router = APIRouter()


@router.get(
    '/',
    name='Get hello world',
    response_model=HelloWorldModel,
)
async def get_hello_world():
    """Simple hello world response"""
    return {
        'project': '{{cookiecutter.project_name}}',
        'message': 'Hello world!'
    }
