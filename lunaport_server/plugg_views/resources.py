# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.resources
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Stataic data like templates and etc
"""

badge = {}
badge['True'] = '''
<svg xmlns="http://www.w3.org/2000/svg" width="123" height="18">
<linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-opacity=".3"/>
    <stop offset="1" stop-opacity=".5"/>
</linearGradient>
<rect rx="4" width="123" height="18" fill="#555"/>
<rect rx="4" x="70" width="53" height="18" fill="#4c1"/>
<path fill="#4c1" d="M70 0h4v18h-4z"/>
<rect rx="4" width="123" height="18" fill="url(#a)"/>
<g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="33" y="13" fill="#010101" fill-opacity=".3">Load test</text>
    <text x="33" y="12">Load test</text>
    <text x="97.5" y="13" fill="#010101" fill-opacity=".3">passing</text>
    <text x="97.5" y="12">passing</text>
</g>
</svg>
'''

badge['True_marked'] = '''
<svg xmlns="http://www.w3.org/2000/svg" width="127" height="18">
<linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-opacity=".3"/>
    <stop offset="1" stop-opacity=".5"/>
</linearGradient>
<rect rx="4" width="127" height="18" fill="#555"/>
<rect rx="4" x="74" width="53" height="18" fill="#4c1"/>
<path fill="#4c1" d="M74 0h4v18h-4z"/>
<rect rx="4" width="127" height="18" fill="url(#a)"/>
<g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="38" y="13" fill="#010101" fill-opacity=".3">Load test ▶</text>
    <text x="38" y="12">Load test ▶</text>
    <text x="99.5" y="13" fill="#010101" fill-opacity=".3">passing</text>
    <text x="99.5" y="12">passing</text>
</g>
</svg>
'''


badge['False'] = '''
<svg xmlns="http://www.w3.org/2000/svg" width="121" height="18">
<linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-opacity=".3"/>
    <stop offset="1" stop-opacity=".5"/>
</linearGradient>
<rect rx="4" width="121" height="18" fill="#555"/>
<rect rx="4" x="69" width="52" height="18" fill="#e05d44"/>
<path fill="#e05d44" d="M69 0h4v18h-4z"/>
<rect rx="4" width="121" height="18" fill="url(#a)"/>
<g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="33" y="13" fill="#010101" fill-opacity=".3">Load test</text>
    <text x="33" y="12">Load test</text>
    <text x="97.5" y="13" fill="#010101" fill-opacity=".3">failing</text>
    <text x="97.5" y="12">failing</text>
</g>
</svg>
'''

badge['False_marked'] = '''
<svg xmlns="http://www.w3.org/2000/svg" width="127" height="18">
<linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-opacity=".3"/>
    <stop offset="1" stop-opacity=".5"/>
</linearGradient>
<rect rx="4" width="127" height="18" fill="#555"/>
<rect rx="4" x="75" width="52" height="18" fill="#e05d44"/>
<path fill="#e05d44" d="M75 0h4v18h-4z"/>
<rect rx="4" width="127" height="18" fill="url(#a)"/>
<g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="38" y="13" fill="#010101" fill-opacity=".3">Load test ▶</text>
    <text x="38" y="12">Load test ▶</text>
    <text x="99.5" y="13" fill="#010101" fill-opacity=".3">failing</text>
    <text x="99.5" y="12">failing</text>
</g>
</svg>
'''
