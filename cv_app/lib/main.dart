import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

void main() {
  runApp(const CarvoariaBistroApp());
}

class CarvoariaBistroApp extends StatelessWidget {
  const CarvoariaBistroApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Carvoaria Bistrô',
      theme: ThemeData(
        fontFamily: 'serif',
        scaffoldBackgroundColor: const Color(0xFFF8F1E5),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF9A3F27),
          brightness: Brightness.light,
        ),
      ),
      home: const BistroHomePage(),
    );
  }
}

class SlideItem {
  const SlideItem({required this.imageAsset, required this.title});

  final String imageAsset;
  final String title;
}

class MenuCategoryData {
  const MenuCategoryData({
    required this.name,
    required this.tagline,
    required this.fromPrice,
    required this.icon,
    required this.accent,
  });

  final String name;
  final String tagline;
  final String fromPrice;
  final IconData icon;
  final Color accent;
}

class BistroHomePage extends StatefulWidget {
  const BistroHomePage({super.key});

  @override
  State<BistroHomePage> createState() => _BistroHomePageState();
}

class _BistroHomePageState extends State<BistroHomePage> {
  final List<SlideItem> _slides = const [
    SlideItem(
      imageAsset:
          'assets/slides/371909529_18014913454790686_4084596035944913294_n.jpg',
      title: 'Ambiente acolhedor e autêntico do Carvoaria Bistrô',
    ),
    SlideItem(
      imageAsset:
          'assets/slides/380704243_18017574511790686_662873138801055601_n.jpg',
      title: 'Sabores especiais para uma experiência memorável',
    ),
    SlideItem(
      imageAsset:
          'assets/slides/462226929_18057637582790686_1515420506234488849_n.jpg',
      title: 'Detalhes que transformam cada visita em celebração',
    ),
    SlideItem(
      imageAsset:
          'assets/slides/463960302_18059162869790686_8890333841464860431_n.jpg',
      title: 'Espaço ideal para encontros, brindes e boa conversa',
    ),
    SlideItem(
      imageAsset:
          'assets/slides/480617955_18071671093790686_7266955140547091412_n.jpg',
      title: 'Cozinha com personalidade e apresentação impecável',
    ),
    SlideItem(
      imageAsset:
          'assets/slides/481214728_18071772928790686_5148583328145169520_n.jpg',
      title: 'O melhor do Carvoaria Bistrô em cada momento',
    ),
  ];

  final List<MenuCategoryData> _menuCategories = const [
    MenuCategoryData(
      name: 'Aperitivos',
      tagline: 'Pequenos sabores para começar em grande estilo',
      fromPrice: 'Desde 6 €',
      icon: Icons.tapas,
      accent: Color(0xFFB25534),
    ),
    MenuCategoryData(
      name: 'Pratos Principais',
      tagline: 'Especialidades da casa com assinatura do chef',
      fromPrice: 'Desde 14 €',
      icon: Icons.dinner_dining,
      accent: Color(0xFF8A3F2D),
    ),
    MenuCategoryData(
      name: 'Bebidas',
      tagline: 'Cocktails, vinhos e bebidas sem alcool',
      fromPrice: 'Desde 3,5 €',
      icon: Icons.local_bar,
      accent: Color(0xFF6E3E88),
    ),
    MenuCategoryData(
      name: 'Sobremesas',
      tagline: 'Final doce com receitas de inspiração artesanal',
      fromPrice: 'Desde 5 €',
      icon: Icons.icecream,
      accent: Color(0xFFAF5E2B),
    ),
  ];

  Timer? _slideTimer;
  int _activeSlide = 0;

  @override
  void initState() {
    super.initState();
    _slideTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      setState(() {
        _activeSlide = (_activeSlide + 1) % _slides.length;
      });
    });
  }

  @override
  void dispose() {
    _slideTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool isMobile = MediaQuery.of(context).size.width < 800;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              _Header(isMobile: isMobile),
              _HeroSlider(
                slides: _slides,
                isMobile: isMobile,
                activeSlide: _activeSlide,
                onSlideChanged: (value) {
                  setState(() {
                    _activeSlide = value;
                  });
                },
              ),
              _MenuSection(categories: _menuCategories),
              const _FloatingImagesSection(),
              const _LocationSection(),
              const _Footer(),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.isMobile});

  final bool isMobile;

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(
        horizontal: isMobile ? 14 : 40,
        vertical: isCompact ? 14 : 18,
      ),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF1E140F), Color(0xFF2E1F18)],
        ),
      ),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 20,
        runSpacing: 8,
        children: [
          const Text(
            'CARVOARIA BISTRÔ',
            style: TextStyle(
              color: Color(0xFFF6E2CF),
              fontSize: 22,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.1,
            ),
          ),
          Wrap(
            spacing: isCompact ? 6 : 0,
            runSpacing: 6,
            children: const [
              _NavChip(label: 'Cardápio'),
              _NavChip(label: 'Localização'),
              _NavChip(label: 'Contato'),
            ],
          ),
        ],
      ),
    );
  }
}

class _NavChip extends StatelessWidget {
  const _NavChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return Container(
      margin: EdgeInsets.only(left: isCompact ? 0 : 10),
      padding: EdgeInsets.symmetric(
        horizontal: isCompact ? 10 : 14,
        vertical: isCompact ? 6 : 7,
      ),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        color: const Color(0x33FFE8D3),
        border: Border.all(color: const Color(0x66F1D2B8)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: Color(0xFFFCE8D7),
          fontSize: isCompact ? 12 : 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _HeroSlider extends StatelessWidget {
  const _HeroSlider({
    required this.slides,
    required this.isMobile,
    required this.activeSlide,
    required this.onSlideChanged,
  });

  final List<SlideItem> slides;
  final bool isMobile;
  final int activeSlide;
  final ValueChanged<int> onSlideChanged;

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(
        horizontal: isMobile ? 8 : 30,
        vertical: isMobile ? 12 : 24,
      ),
      child: SizedBox(
        height: isCompact ? 290 : (isMobile ? 330 : 460),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(isCompact ? 16 : 22),
          child: GestureDetector(
            onHorizontalDragEnd: (details) {
              if (details.primaryVelocity == null) return;
              if (details.primaryVelocity! < -300) {
                onSlideChanged((activeSlide + 1) % slides.length);
              } else if (details.primaryVelocity! > 300) {
                onSlideChanged(
                  (activeSlide - 1 + slides.length) % slides.length,
                );
              }
            },
            child: Stack(
              children: [
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 900),
                  transitionBuilder: (child, animation) =>
                      FadeTransition(opacity: animation, child: child),
                  child: Stack(
                    key: ValueKey(activeSlide),
                    fit: StackFit.expand,
                    children: [
                      Image.asset(
                        slides[activeSlide].imageAsset,
                        fit: BoxFit.cover,
                        width: double.infinity,
                        height: double.infinity,
                      ),
                      const DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.bottomCenter,
                            end: Alignment.topCenter,
                            colors: [Color(0xD9311A12), Color(0x33000000)],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                Positioned(
                  left: isMobile ? 14 : 22,
                  right: isMobile ? 14 : 22,
                  bottom: isMobile ? 18 : 24,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Carvoaria Bistrô',
                        style: TextStyle(
                          color: Color(0xFFFFEDE0),
                          fontSize: 32,
                          fontWeight: FontWeight.w800,
                          height: 1,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        slides[activeSlide].title,
                        maxLines: isCompact ? 2 : 3,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: Color(0xFFFFF4EC),
                          fontSize: isCompact ? 14 : 17,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: List.generate(slides.length, (index) {
                          final bool selected = index == activeSlide;
                          return AnimatedContainer(
                            duration: const Duration(milliseconds: 250),
                            margin: const EdgeInsets.only(right: 8),
                            width: selected ? 28 : 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: selected
                                  ? const Color(0xFFFFD1A8)
                                  : const Color(0x88FFFFFF),
                              borderRadius: BorderRadius.circular(999),
                            ),
                          );
                        }),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _MenuSection extends StatelessWidget {
  const _MenuSection({required this.categories});

  final List<MenuCategoryData> categories;

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(14, isCompact ? 6 : 10, 14, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Align(
            alignment: Alignment.center,
            child: Text(
              'Menu',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 34,
                color: Color(0xFF2E1C14),
                fontWeight: FontWeight.w800,
              ).copyWith(fontSize: isCompact ? 28 : 34),
            ),
          ),
          SizedBox(height: isCompact ? 4 : 6),
          Align(
            alignment: Alignment.center,
            child: Text(
              'Escolha uma categoria para explorar a carta.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 16,
                color: Color(0xFF6D5141),
                fontWeight: FontWeight.w500,
              ).copyWith(fontSize: isCompact ? 14 : 16),
            ),
          ),
          SizedBox(height: isCompact ? 12 : 16),
          LayoutBuilder(
            builder: (context, constraints) {
              final bool isMobile = constraints.maxWidth < 760;
              final double cardWidth = isMobile
                  ? constraints.maxWidth
                  : (constraints.maxWidth - 12) / 2;

              return Wrap(
                spacing: 12,
                runSpacing: 12,
                children: categories
                    .map(
                      (category) => SizedBox(
                        width: cardWidth,
                        child: _MenuCategoryCard(category: category),
                      ),
                    )
                    .toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _MenuCategoryCard extends StatelessWidget {
  const _MenuCategoryCard({required this.category});

  final MenuCategoryData category;

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return InkWell(
      onTap: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => MenuCategoryPage(category: category),
          ),
        );
      },
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: EdgeInsets.all(isCompact ? 14 : 18),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          gradient: LinearGradient(
            colors: [category.accent, const Color(0xFF2D1C14)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          boxShadow: const [
            BoxShadow(
              blurRadius: 18,
              offset: Offset(0, 8),
              color: Color(0x22000000),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: isCompact ? 40 : 44,
                  height: isCompact ? 40 : 44,
                  decoration: const BoxDecoration(
                    color: Color(0x22FFFFFF),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(category.icon, color: const Color(0xFFFFF3E9)),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    category.name,
                    style: TextStyle(
                      color: Color(0xFFFFF5ED),
                      fontSize: isCompact ? 18 : 21,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: isCompact ? 8 : 10),
            Text(
              category.tagline,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: Color(0xFFFADCC6),
                fontSize: isCompact ? 13 : 14,
                height: 1.3,
              ),
            ),
            SizedBox(height: isCompact ? 10 : 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  category.fromPrice,
                  style: TextStyle(
                    color: Color(0xFFFFE6CC),
                    fontSize: isCompact ? 15 : 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Row(
                  children: [
                    Text(
                      'Ver área',
                      style: TextStyle(
                        color: Color(0xFFFFE6CC),
                        fontWeight: FontWeight.w600,
                        fontSize: isCompact ? 12 : 14,
                      ),
                    ),
                    const SizedBox(width: 5),
                    Icon(
                      Icons.arrow_forward_rounded,
                      color: Color(0xFFFFE6CC),
                      size: isCompact ? 16 : 18,
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class MenuCategoryPage extends StatelessWidget {
  const MenuCategoryPage({super.key, required this.category});

  final MenuCategoryData category;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(category.name),
        backgroundColor: const Color(0xFF2E1F18),
        foregroundColor: const Color(0xFFFCEBDB),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(category.icon, size: 68, color: category.accent),
              const SizedBox(height: 16),
              Text(
                category.name,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF2E1C14),
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Esta área será dedicada ao menu completo de ${category.name.toLowerCase()} em breve.',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, color: Color(0xFF5E4738)),
              ),
              const SizedBox(height: 16),
              Text(
                category.fromPrice,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF9D4429),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LocationSection extends StatelessWidget {
  const _LocationSection();

  static final Uri _mapsUri = Uri.parse(
    'https://www.google.com/maps/search/?api=1&query=Tv.%20da%20Cancella%201%207000-629%20%C3%89vora%20Portugal',
  );

  static final Uri _whatsAppUri = Uri.parse('https://wa.me/351932196982');

  static final Uri _instagramUri = Uri.parse(
    'https://www.instagram.com/carvoariabistro/',
  );

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return Container(
      width: double.infinity,
      margin: EdgeInsets.fromLTRB(14, 6, 14, 20),
      padding: EdgeInsets.all(isCompact ? 14 : 18),
      decoration: BoxDecoration(
        color: const Color(0xFFFBEBDD),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Localização e Horários',
            style: const TextStyle(
              fontSize: 30,
              color: Color(0xFF2E1C14),
              fontWeight: FontWeight.w800,
            ).copyWith(fontSize: isCompact ? 24 : 30),
          ),
          SizedBox(height: isCompact ? 10 : 12),
          Text(
            'Tv. da Cancella 1, 7000-629 Évora - Portugal',
            style: TextStyle(
              fontSize: isCompact ? 14 : 16,
              color: const Color(0xFF463426),
            ),
          ),
          SizedBox(height: isCompact ? 6 : 8),
          Text(
            'Ter a Sáb: 17h às 2h',
            style: TextStyle(fontSize: isCompact ? 14 : 15),
          ),
          SizedBox(height: isCompact ? 12 : 14),
          Text(
            'Siga-nos e entre em contato',
            style: TextStyle(
              fontSize: isCompact ? 15 : 17,
              color: Color(0xFF5B4334),
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: isCompact ? 10 : 12),
          Wrap(
            spacing: 14,
            runSpacing: 14,
            children: [
              _SocialIconButton(
                brand: SocialBrand.maps,
                label: 'Google Maps',
                url: _mapsUri,
              ),
              _SocialIconButton(
                brand: SocialBrand.whatsApp,
                label: 'WhatsApp',
                url: _whatsAppUri,
              ),
              _SocialIconButton(
                brand: SocialBrand.instagram,
                label: 'Instagram',
                url: _instagramUri,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

enum SocialBrand { maps, whatsApp, instagram }

class _SocialIconButton extends StatelessWidget {
  const _SocialIconButton({
    required this.brand,
    required this.label,
    required this.url,
  });

  final SocialBrand brand;
  final String label;
  final Uri url;

  List<Color> _brandGradient() {
    switch (brand) {
      case SocialBrand.maps:
        return const [Color(0xFF34A853), Color(0xFF4285F4), Color(0xFFEA4335)];
      case SocialBrand.whatsApp:
        return const [Color(0xFF22C55E), Color(0xFF128C7E)];
      case SocialBrand.instagram:
        return const [
          Color(0xFFFEDA75),
          Color(0xFFFA7E1E),
          Color(0xFFD62976),
          Color(0xFF4F5BD5),
        ];
    }
  }

  Widget _brandGlyph() {
    switch (brand) {
      case SocialBrand.maps:
        return const Icon(Icons.place_rounded, size: 34, color: Colors.white);
      case SocialBrand.whatsApp:
        return const Stack(
          alignment: Alignment.center,
          children: [
            Icon(Icons.chat_bubble_rounded, size: 36, color: Colors.white),
            Padding(
              padding: EdgeInsets.only(top: 1),
              child: Icon(Icons.phone, size: 18, color: Color(0xFF128C7E)),
            ),
          ],
        );
      case SocialBrand.instagram:
        return Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 31,
              height: 31,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 2.6),
                borderRadius: BorderRadius.circular(9),
              ),
            ),
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2.2),
              ),
            ),
            Positioned(
              top: 9,
              right: 8,
              child: Container(
                width: 5,
                height: 5,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ],
        );
    }
  }

  Future<void> _openLink() async {
    if (!await launchUrl(url, mode: LaunchMode.platformDefault)) {
      throw Exception('Não foi possível abrir o link: $url');
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return InkWell(
      onTap: _openLink,
      borderRadius: BorderRadius.circular(999),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: isCompact ? 64 : 78,
            height: isCompact ? 64 : 78,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(isCompact ? 18 : 22),
              gradient: LinearGradient(
                colors: _brandGradient(),
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              border: Border.all(color: const Color(0x66FFFFFF), width: 1.2),
              boxShadow: const [
                BoxShadow(
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                  color: Color(0x30000000),
                ),
              ],
            ),
            child: Center(child: _brandGlyph()),
          ),
          SizedBox(height: isCompact ? 6 : 8),
          Text(
            label,
            style: TextStyle(
              color: Color(0xFF4A362B),
              fontWeight: FontWeight.w700,
              fontSize: isCompact ? 12 : 13,
            ),
          ),
        ],
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  const _Footer();

  @override
  Widget build(BuildContext context) {
    final bool isCompact = MediaQuery.of(context).size.width < 430;

    return Container(
      width: double.infinity,
      color: const Color(0xFF241813),
      padding: EdgeInsets.symmetric(
        horizontal: 14,
        vertical: isCompact ? 14 : 18,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Carvoaria Bistrô | @carvoariabistro | Reservas: +351 932196982',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Color(0xFFF5DCC9),
              fontSize: isCompact ? 12 : 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          SizedBox(height: isCompact ? 8 : 10),
          GestureDetector(
            onTap: () => launchUrl(
              Uri.parse('https://deploylabz.com'),
              mode: LaunchMode.externalApplication,
            ),
            child: RichText(
              textAlign: TextAlign.center,
              text: TextSpan(
                style: TextStyle(
                  fontSize: isCompact ? 11 : 12,
                  color: Color(0xFF8C6E5A),
                ),
                children: [
                  TextSpan(text: 'Desenvolvido por '),
                  TextSpan(
                    text: 'deploylabz.com',
                    style: TextStyle(
                      color: Color(0xFFD4956A),
                      fontWeight: FontWeight.w600,
                      decoration: TextDecoration.underline,
                      decorationColor: Color(0xFFD4956A),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FloatingImagesSection extends StatelessWidget {
  const _FloatingImagesSection({Key? key}) : super(key: key);

  static const List<String> _imagePaths = [
    'assets/carvoarianovasfotos/371909529_18014913454790686_4084596035944913294_n.jpg',
    'assets/carvoarianovasfotos/380704243_18017574511790686_662873138801055601_n.jpg',
    'assets/carvoarianovasfotos/462226929_18057637582790686_1515420506234488849_n.jpg',
  ];

  @override
  Widget build(BuildContext context) {
    final double screenW = MediaQuery.of(context).size.width;
    final bool isMobile = screenW < 800;
    final double hPad = isMobile ? 14 : 40;
    final double margin = isMobile ? 8 : 12;
    // Size each image so the three always fit within the screen width on
    // mobile (was a fixed 110px, which overflowed on narrow phones).
    final double available = screenW - hPad * 2 - margin * 2 * _imagePaths.length;
    final double imgSize =
        isMobile ? (available / _imagePaths.length).clamp(72.0, 130.0) : 180.0;
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(
        horizontal: hPad,
        vertical: 24,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(_imagePaths.length, (index) {
          return Transform.translate(
            offset: Offset(0, index.isOdd ? -18 : 0),
            child: Container(
              margin: EdgeInsets.symmetric(horizontal: margin),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.18),
                    blurRadius: 18,
                    offset: Offset(0, 8),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: Image.asset(
                  _imagePaths[index],
                  width: imgSize,
                  height: imgSize,
                  fit: BoxFit.cover,
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}
