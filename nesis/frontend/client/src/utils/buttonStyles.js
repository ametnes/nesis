import { device } from './breakpoints';
// import { css } from 'styled-components/macro';
import { css } from 'styled-components';

export const ButtonColor = {
  Primary: {
    bg: 'primary',
    fg: 'white',
    border: 'primary',
    hoverBg: 'primaryDark',
    hoverFg: 'white',
  },
  PrimaryWithBorder: {
    bg: 'primary',
    fg: 'white',
    border: () => 'rgba(255, 255, 255, 0.3)',
    hoverBg: 'primary',
    hoverFg: 'white',
    hoverBorder: 'white',
  },
  Secondary: {
    bg: 'white',
    fg: 'primary',
    border: 'white',
    hoverBg: () => '#EBEDFF',
    hoverBorder: () => '#EBEDFF',
  },
  SecondaryWithBorder: {
    bg: 'white',
    fg: 'primary',
    border: 'primary',
    hoverBg: () => '#EBEDFF',
    hoverBorder: 'primary',
  },
};

function applyColor(colorName, fallbackColorName) {
  return function ({ theme, $color }) {
    if ($color[colorName]) {
      return loadColorOrFn($color[colorName], theme);
    } else if ($color[fallbackColorName]) {
      return loadColorOrFn($color[fallbackColorName], theme);
    } else {
      return 'black';
    }
  };
}

function loadColorOrFn(colorOption, theme) {
  if (typeof colorOption === 'function') {
    return colorOption(theme);
  } else {
    return theme[colorOption];
  }
}
export const buttonStyles = css`
  background-color: ${applyColor('bg')};
  color: ${applyColor('fg')};
  padding: 8px 16px;
  border-radius: 100px;
  text-decoration: none;
  font-weight: 500;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  min-width: 270px;
  min-height: 61px;
  box-sizing: border-box;
  border: 2px solid ${applyColor('border', 'fg')};
  width: ${(props) => (props.$fitContent ? 'fit-content' : 'auto')};

  &:hover {
    background-color: ${applyColor('hoverBg', 'bg')};
    color: ${applyColor('hoverFg', 'fg')};
    border: 2px solid ${applyColor('hoverBorder', 'border')};
  }

  &:disabled {
    opacity: 50%;
    cursor: not-allowed;
  }

  @media ${device.tablet} {
    min-width: 150px;
  }

  @media ${device.laptop} {
    min-width: 200px;
  }
`;
