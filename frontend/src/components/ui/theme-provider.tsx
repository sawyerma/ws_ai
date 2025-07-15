import { ReactNode } from "react";
import { ThemeProviderContext, useThemeLogic } from "../../hooks/use-theme";

interface ThemeProviderProps {
  children: ReactNode;
}

const ThemeProvider = ({ children }: ThemeProviderProps) => {
  const themeLogic = useThemeLogic();

  return (
    <ThemeProviderContext.Provider value={themeLogic}>
      {children}
    </ThemeProviderContext.Provider>
  );
};

export default ThemeProvider;
