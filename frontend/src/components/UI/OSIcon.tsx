import React from 'react';

interface OSIconProps {
  distribution: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * 操作系统图标组件
 * 使用 Simple Icons CDN 提供的 SVG 图标
 */
export const OSIcon: React.FC<OSIconProps> = ({ distribution, size = 'md', className = '' }) => {
  // 尺寸映射
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  // 获取操作系统图标信息
  const getOSIconInfo = (dist: string): { icon: string; color: string; name: string } => {
    const distLower = dist.toLowerCase();

    // Ubuntu
    if (distLower.includes('ubuntu')) {
      return { icon: 'ubuntu', color: '#E95420', name: 'Ubuntu' };
    }

    // Debian
    if (distLower.includes('debian')) {
      return { icon: 'debian', color: '#A81D33', name: 'Debian' };
    }

    // CentOS
    if (distLower.includes('centos')) {
      return { icon: 'centos', color: '#262577', name: 'CentOS' };
    }

    // Red Hat / RHEL
    if (distLower.includes('red hat') || distLower.includes('rhel')) {
      return { icon: 'redhat', color: '#EE0000', name: 'Red Hat' };
    }

    // Rocky Linux
    if (distLower.includes('rocky')) {
      return { icon: 'rockylinux', color: '#10B981', name: 'Rocky Linux' };
    }

    // AlmaLinux
    if (distLower.includes('alma')) {
      return { icon: 'almalinux', color: '#000000', name: 'AlmaLinux' };
    }

    // Fedora
    if (distLower.includes('fedora')) {
      return { icon: 'fedora', color: '#51A2DA', name: 'Fedora' };
    }

    // SUSE / openSUSE
    if (distLower.includes('suse')) {
      return { icon: 'opensuse', color: '#73BA25', name: 'openSUSE' };
    }

    // Arch Linux
    if (distLower.includes('arch')) {
      return { icon: 'archlinux', color: '#1793D1', name: 'Arch Linux' };
    }

    // Alpine Linux
    if (distLower.includes('alpine')) {
      return { icon: 'alpinelinux', color: '#0D597F', name: 'Alpine Linux' };
    }

    // Gentoo
    if (distLower.includes('gentoo')) {
      return { icon: 'gentoo', color: '#54487A', name: 'Gentoo' };
    }

    // Kali Linux
    if (distLower.includes('kali')) {
      return { icon: 'kalilinux', color: '#557C94', name: 'Kali Linux' };
    }

    // Linux Mint
    if (distLower.includes('mint')) {
      return { icon: 'linuxmint', color: '#87CF3E', name: 'Linux Mint' };
    }

    // Manjaro
    if (distLower.includes('manjaro')) {
      return { icon: 'manjaro', color: '#35BF5C', name: 'Manjaro' };
    }

    // 默认 Linux
    return { icon: 'linux', color: '#FCC624', name: 'Linux' };
  };

  const iconInfo = getOSIconInfo(distribution);
  const iconUrl = `https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/${iconInfo.icon}.svg`;

  return (
    <div 
      className={`${sizeMap[size]} ${className} inline-block`}
      style={{
        WebkitMaskImage: `url(${iconUrl})`,
        WebkitMaskRepeat: 'no-repeat',
        WebkitMaskSize: 'contain',
        WebkitMaskPosition: 'center',
        maskImage: `url(${iconUrl})`,
        maskRepeat: 'no-repeat',
        maskSize: 'contain',
        maskPosition: 'center',
        backgroundColor: iconInfo.color,
        filter: `drop-shadow(0 0 2px ${iconInfo.color}40)`
      }}
      title={distribution}
      aria-label={iconInfo.name}
    />
  );
};

/**
 * 获取操作系统颜色（用于文字或背景）
 */
export const getOSColor = (distribution: string): string => {
  const distLower = distribution.toLowerCase();

  if (distLower.includes('ubuntu')) return '#E95420';
  if (distLower.includes('debian')) return '#A81D33';
  if (distLower.includes('centos')) return '#262577';
  if (distLower.includes('red hat') || distLower.includes('rhel')) return '#EE0000';
  if (distLower.includes('rocky')) return '#10B981';
  if (distLower.includes('alma')) return '#000000';
  if (distLower.includes('fedora')) return '#51A2DA';
  if (distLower.includes('suse')) return '#73BA25';
  if (distLower.includes('arch')) return '#1793D1';
  if (distLower.includes('alpine')) return '#0D597F';
  if (distLower.includes('gentoo')) return '#54487A';
  if (distLower.includes('kali')) return '#557C94';
  if (distLower.includes('mint')) return '#87CF3E';
  if (distLower.includes('manjaro')) return '#35BF5C';

  return '#FCC624'; // 默认 Linux 黄色
};
