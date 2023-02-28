
from rhombus.lib import tags as t
from pyramid.request import Request
from pyramid.url import route_url


class MenuNav(object):

    menutree = []
    menu_cache = None

    def __init__(self):

        self.menutree = [
            ('Data', [
                ('Collection', 'url:/collection'),
                ('Sample', 'url:/sample'),
                ('Institution', 'url:/institution'),
                t.hr,
                ('Plate', 'url:/plate')
            ]
            ),
            ('Analysis', [
            ]
            ),
            ('Upload', 'url:/upload'
             ),
            ('Tools', 'url:/tools'
             ),
            ('Help', 'url:/help/index.rst'
             )
        ]

        self.menu_cache = self.html()

    def generate_href_from_spec(self, spec):
        if spec.startswith('url:'):
            href = spec[4:]
        else:
            raise ValueError('cannot convert spec to URL')
        return href

    def html(self):

        html = t.ul(class_='navbar-nav me-auto')

        for menuitem in self.menutree:
            label, spec = menuitem
            if type(spec) is list:
                item_html = t.li(class_='nav-item active dropdown').add(
                    t.a(label, name=f'navbar{label}menu', id=f'navbar{label}menu',
                        class_='nav-link dropdown-toggle', role='button',
                        ** {'data-bs-toggle': 'dropdown', 'aria-expanded': 'false'}
                        )
                )
                submenu_html = t.ul(class_='dropdown-menu',
                                    **{'aria-labelledby': f'navbar{label}menu'})
                for subitem in spec:
                    if type(subitem) is tuple:
                        label, href = subitem[0], self.generate_href_from_spec(subitem[1])
                        submenu_html.add(
                            t.li(
                                t.a(label, href=href, class_='dropdown-item')
                            )
                        )
                    else:
                        submenu_html.add(t.li(subitem))

                item_html.add(submenu_html)

            elif type(spec) is str:
                href = self.generate_href_from_spec(spec)
                item_html = t.li(class_='nav-item').add(
                    t.a(label, class_='nav-link', href=href)
                )
            else:
                raise ValueError('unknown menu item spec type in menutree')

            html.add(item_html)

        return html

    def add_menu(self, tag, newitem, after=False):

        for idx, menuitem in enumerate(self.menutree):
            if type(menuitem) is tuple:
                if menuitem[0] == tag:
                    self.menutree.insert(idx if not after else idx + 1, newitem)
                    break
                if type(menuitem[1] == list):
                    for idx2, submenuitem in enumerate(menuitem[1]):
                        if type(submenuitem) is tuple:
                            if submenuitem[0] == tag:
                                if type(newitem) is list:
                                    for pos, item in enumerate(newitem):
                                        menuitem[1].insert(
                                            (idx2 if not after else idx2 + 1) + pos,
                                            item
                                        )
                                else:
                                    menuitem[1].insert(idx2 if not after else idx2 + 1, newitem)
                                break

        self.menu_cache = self.html()

        return self


__menunav__ = MenuNav()


def get_menunav():
    return __menunav__


def main_menu():
    return __menunav__.menu_cache

# EOF
