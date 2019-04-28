# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginator_helper(request, object_list, per_page=10):
    '''分页辅助函数'''
    paginator = Paginator(object_list, per_page)
    page = request.GET.get('page', 1)
    try:
        page = paginator.page(page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    page_range_ex = []
    if paginator.num_pages > settings.PAGE_RANGE:
        left = settings.PAGE_RANGE / 2
        right = settings.PAGE_RANGE - left
        if page.number > paginator.num_pages - settings.PAGE_RANGE / 2:
            right = paginator.num_pages - page.number
            left = settings.PAGE_RANGE - right
        elif page.number < settings.PAGE_RANGE / 2:
            left = page.number
            right = settings.PAGE_RANGE - left
        for page_number in range(1, paginator.num_pages + 1):
            if page_number < settings.MARGIN_PAGES:
                page_range_ex.append(page_number)
                continue
            if page_number > paginator.num_pages - settings.MARGIN_PAGES:
                page_range_ex.append(page_number)
                continue
            if (page_number >= page.number - left) and (
                    page_number <= page.number + right):
                page_range_ex.append(page_number)
                continue
            if page_range_ex[-1]:
                page_range_ex.append(None)
        # 由于paginator.page_range为只读, 给page绑定页码列表
        page.page_range_ex = page_range_ex
    else:
        page.page_range_ex = paginator.page_range
    return page
